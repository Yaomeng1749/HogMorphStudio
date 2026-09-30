#!/usr/bin/env python3
"""Train a small multi-label phenotype baseline from a gated JSONL manifest.

Requires torch, torchvision, Pillow. This script refuses sparse or leaked splits;
it prints measured values only after a model has actually been trained.
"""

import argparse
import hashlib
import json
import random
import math
from collections import defaultdict
from pathlib import Path

from prepare_training_manifest import validate


SPLIT_NAMES = ("train", "validation", "test")
MINIMUMS = (5, 3, 3)


def validate_individual_labels(rows):
    """Reject an individual whose reviewed photos disagree on an explicit label."""
    observed = defaultdict(dict)
    for row in rows:
        individual = row["individual_id"]
        for class_id, value in row["labels"].items():
            previous = observed[individual].get(class_id)
            if previous is not None and previous != value:
                raise ValueError(
                    f"Contradictory explicit labels for individual {individual!r}, "
                    f"class {class_id!r}: both {previous} and {value}"
                )
            observed[individual][class_id] = value


def read_manifest(path):
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not rows:
        raise ValueError("Empty manifest. Run prepare_training_manifest.py first.")
    hashes = set()
    for row in rows:
        _, reasons = validate(row, path.resolve().parent)
        if reasons:
            raise ValueError(f"Ungated manifest row {row.get('id')}: {', '.join(reasons)}")
        digest = hashlib.sha256(Path(row["image"]).read_bytes()).hexdigest()
        if digest in hashes:
            raise ValueError(f"Duplicate image bytes: {row.get('id')}")
        hashes.add(digest)
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate image record IDs")
    return rows


def grouped_split(rows, seed):
    validate_individual_labels(rows)
    groups = defaultdict(list)
    for row in rows:
        groups[row["individual_id"]].append(row)
    ids = sorted(groups)
    n = len(ids)
    n_train, n_val = round(n * .70), round(n * .15)
    sizes = (n_train, n_val, n - n_train - n_val)
    if any(size == 0 for size in sizes):
        raise ValueError("Need enough distinct individuals for train/validation/test")

    # Optimize by whole individual. The primary objective is the number of
    # classes meeting every split minimum; the secondary objective rewards
    # support toward those minima without allowing abundant classes to dominate.
    labels = sorted({key for row in rows for key in row["labels"]})
    profiles = {
        individual: {
            class_id: next((row["labels"][class_id] for row in group
                            if class_id in row["labels"]), None)
            for class_id in labels
        }
        for individual, group in groups.items()
    }
    ordered_ids = sorted(groups)

    def objective(assignment):
        counts = {class_id: [[0, 0] for _ in SPLIT_NAMES] for class_id in labels}
        for individual, split in assignment.items():
            for class_id, value in profiles[individual].items():
                if value is not None:
                    counts[class_id][split][value] += 1
        eligible = 0
        support = 0
        for class_id in labels:
            passed = True
            for split, minimum in enumerate(MINIMUMS):
                positive, negative = counts[class_id][split][1], counts[class_id][split][0]
                passed &= positive >= minimum and negative >= minimum
                support += min(positive, minimum) + min(negative, minimum)
            eligible += int(passed)
        return eligible, support

    rng = random.Random(seed)
    best_assignment, best_score = None, (-1, -1)
    # Bounded randomized swap search: deterministic for a given seed and exact
    # partition sizes, while adapting the split to rare positive/negative labels.
    restarts = 48
    proposals_per_restart = max(300, min(1600, n * 16))
    for _ in range(restarts):
        shuffled = ordered_ids[:]
        rng.shuffle(shuffled)
        assignment = {}
        cursor = 0
        for split, size in enumerate(sizes):
            for individual in shuffled[cursor:cursor + size]:
                assignment[individual] = split
            cursor += size
        score = objective(assignment)
        for _ in range(proposals_per_restart):
            left, right = rng.sample(ordered_ids, 2)
            if assignment[left] == assignment[right]:
                continue
            left_split, right_split = assignment[left], assignment[right]
            assignment[left], assignment[right] = right_split, left_split
            candidate = objective(assignment)
            if candidate > score:
                score = candidate
            else:
                assignment[left], assignment[right] = left_split, right_split
            if score > best_score:
                best_assignment, best_score = assignment.copy(), score

    if best_assignment is None:
        raise ValueError("Could not construct grouped train/validation/test split")
    partitions = [[] for _ in SPLIT_NAMES]
    for individual in ordered_ids:
        partitions[best_assignment[individual]].extend(groups[individual])
    return partitions


def split_feasibility(rows):
    """Explain sample-size and per-class support constraints before torch import."""
    validate_individual_labels(rows)
    n = len({row["individual_id"] for row in rows})
    sizes = (round(n * .70), round(n * .15), n - round(n * .70) - round(n * .15))
    class_ids = sorted({key for row in rows for key in row["labels"]})
    profiles = defaultdict(dict)
    for row in rows:
        for class_id, value in row["labels"].items():
            profiles[row["individual_id"]][class_id] = value
    diagnostics = {}
    for class_id in class_ids:
        positive = sum(profile.get(class_id) == 1 for profile in profiles.values())
        negative = sum(profile.get(class_id) == 0 for profile in profiles.values())
        theoretically_possible = (positive >= sum(MINIMUMS) and
                                  negative >= sum(MINIMUMS) and
                                  all(size >= minimum * 2
                                      for size, minimum in zip(sizes, MINIMUMS)))
        diagnostics[class_id] = {
            "positive_individuals": positive,
            "explicit_negative_individuals": negative,
            "minimum_positive_and_negative_per_split": dict(zip(SPLIT_NAMES, MINIMUMS)),
            "possible_by_global_counts": theoretically_possible,
        }
    minimum_capacity = None
    for count in range(1, 10000):
        candidate_sizes = (round(count * .70), round(count * .15),
                           count - round(count * .70) - round(count * .15))
        if all(size >= minimum * 2
               for size, minimum in zip(candidate_sizes, MINIMUMS)):
            minimum_capacity = count
            break
    return {
        "individuals": n,
        "partition_individuals": dict(zip(SPLIT_NAMES, sizes)),
        "minimum_individuals_for_split_capacity": minimum_capacity,
        "classes": diagnostics,
    }


def eligible_classes(parts):
    all_classes = sorted({key for part in parts for row in part for key in row["labels"]})
    allowed, omitted = [], {}
    for key in all_classes:
        counts = []
        for part in parts:
            positives = {r["individual_id"] for r in part if r["labels"].get(key) == 1}
            negatives = {r["individual_id"] for r in part if r["labels"].get(key) == 0}
            counts.append({"positive_individuals": len(positives),
                           "negative_individuals": len(negatives)})
        minima = MINIMUMS
        if all(c["positive_individuals"] >= minimum and
               c["negative_individuals"] >= minimum
               for c, minimum in zip(counts, minima)):
            allowed.append(key)
        else:
            omitted[key] = {"reason": "insufficient positive or explicit negative individuals per split; minimum train/val/test = 5/3/3 each",
                            "split_counts": counts}
    return allowed, omitted


def split_class_support(parts):
    report = {}
    class_ids = sorted({key for part in parts for row in part for key in row["labels"]})
    for class_id in class_ids:
        counts = []
        for part in parts:
            positives = {row["individual_id"] for row in part
                         if row["labels"].get(class_id) == 1}
            negatives = {row["individual_id"] for row in part
                         if row["labels"].get(class_id) == 0}
            counts.append({"positive_individuals": len(positives),
                           "explicit_negative_individuals": len(negatives)})
        report[class_id] = dict(zip(SPLIT_NAMES, counts))
    return report


def metrics(y_true, scores, threshold):
    pairs = [(int(y), float(s)) for y, s in zip(y_true, scores) if y in (0, 1)]
    positives = sum(y for y, _ in pairs)
    negatives = len(pairs) - positives
    if not positives or not negatives:
        return {"positive_images": positives, "negative_images": negatives,
                "precision": None, "recall": None, "f1": None,
                "average_precision": None}
    tp = sum(y == 1 and s >= threshold for y, s in pairs)
    fp = sum(y == 0 and s >= threshold for y, s in pairs)
    fn = positives - tp
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    # Evaluate after consuming all examples at a tied score threshold so AP
    # does not depend on input row order within a tie.
    threshold_groups = defaultdict(lambda: [0, 0])
    for label, score in pairs:
        threshold_groups[score][0] += label
        threshold_groups[score][1] += 1
    seen_positives = seen_examples = 0
    previous_recall = average_precision = 0.0
    for score in sorted(threshold_groups, reverse=True):
        group_positives, group_examples = threshold_groups[score]
        seen_positives += group_positives
        seen_examples += group_examples
        recall_at_threshold = seen_positives / positives
        precision_at_threshold = seen_positives / seen_examples
        average_precision += ((recall_at_threshold - previous_recall) *
                              precision_at_threshold)
        previous_recall = recall_at_threshold
    return {"positive_images": positives, "negative_images": negatives,
            "precision": round(precision, 4), "recall": round(recall, 4),
            "f1": round(f1, 4), "average_precision": round(average_precision, 4)}


def _percentile(values, probability):
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def group_bootstrap_intervals(y_true, scores, individual_ids, threshold,
                              seed=42, iterations=500):
    """Percentile intervals from resampling whole held-out individuals."""
    if not (len(y_true) == len(scores) == len(individual_ids)):
        raise ValueError("Bootstrap labels, scores, and individual IDs must align")
    grouped = defaultdict(list)
    for truth, score, individual in zip(y_true, scores, individual_ids):
        grouped[individual].append((truth, score))
    individuals = sorted(grouped)
    if not individuals or iterations < 1:
        return {"resampling_unit": "individual_id", "individuals": len(individuals),
                "iterations": iterations,
                "valid_iterations": {name: 0 for name in
                                     ("precision", "recall", "f1", "average_precision")},
                "intervals_95": {},
                "conditioning_policy": "each metric interval uses only resamples where that metric is defined"}
    rng = random.Random(seed)
    values = {name: [] for name in ("precision", "recall", "f1", "average_precision")}
    for _ in range(iterations):
        sampled = rng.choices(individuals, k=len(individuals))
        sample = [item for individual in sampled for item in grouped[individual]]
        report = metrics([item[0] for item in sample],
                         [item[1] for item in sample], threshold)
        for name in ("precision", "recall", "f1", "average_precision"):
            if report[name] is not None:
                values[name].append(report[name])
    intervals = {
        name: ({"low": round(_percentile(observations, .025), 4),
                "high": round(_percentile(observations, .975), 4)}
               if observations else None)
        for name, observations in values.items()
    }
    return {"resampling_unit": "individual_id", "individuals": len(individuals),
            "iterations": iterations,
            "valid_iterations": {name: len(observations)
                                 for name, observations in values.items()},
            "intervals_95": intervals,
            "conditioning_policy": "each metric interval uses only resamples where that metric is defined"}


def group_bootstrap_macro_f1(y_true_by_class, scores_by_class, ids_by_class,
                            thresholds, seed=42, iterations=500):
    """Macro-F1 percentile interval using the same animal resample per class."""
    all_ids = sorted({individual for class_ids in ids_by_class
                      for individual in class_ids})
    if not all_ids or iterations < 1:
        return {"resampling_unit": "individual_id", "individuals": len(all_ids),
                "iterations": iterations, "valid_iterations": 0,
                "interval_95": None,
                "conditioning_policy": "retain a resample only when every evaluated class has both positive and negative examples"}
    rng = random.Random(seed)
    per_class = []
    for truth, scores, ids in zip(y_true_by_class, scores_by_class, ids_by_class):
        grouped = defaultdict(list)
        for y, score, individual in zip(truth, scores, ids):
            grouped[individual].append((y, score))
        per_class.append(grouped)
    macro_values = []
    for _ in range(iterations):
        sampled_ids = rng.choices(all_ids, k=len(all_ids))
        class_f1 = []
        for class_index, grouped in enumerate(per_class):
            sample = [item for individual in sampled_ids
                      for item in grouped.get(individual, [])]
            result = metrics([item[0] for item in sample],
                             [item[1] for item in sample], thresholds[class_index])
            if result["f1"] is not None:
                class_f1.append(result["f1"])
        if len(class_f1) == len(per_class):
            macro_values.append(sum(class_f1) / len(class_f1))
    interval = ({"low": round(_percentile(macro_values, .025), 4),
                 "high": round(_percentile(macro_values, .975), 4)}
                if macro_values else None)
    return {"resampling_unit": "individual_id", "individuals": len(all_ids),
            "iterations": iterations, "valid_iterations": len(macro_values),
            "interval_95": interval,
            "conditioning_policy": "retain a resample only when every evaluated class has both positive and negative examples"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-pretrained", action="store_true",
                        help="Train from random weights; generally poor for this small dataset")
    args = parser.parse_args()
    if args.epochs < 1 or args.batch_size < 1:
        parser.error("epochs and batch-size must be positive")
    rows = read_manifest(args.manifest)
    individuals = {r["individual_id"] for r in rows}
    if len(rows) < 100 or len(individuals) < 30:
        raise SystemExit(f"Training gate: need >=100 eligible images and >=30 individuals; "
                         f"found {len(rows)} images and {len(individuals)} individuals")
    feasibility = split_feasibility(rows)
    if feasibility["minimum_individuals_for_split_capacity"] is None or len(individuals) < feasibility["minimum_individuals_for_split_capacity"]:
        raise SystemExit(
            "Training gate: split capacity cannot satisfy the required per-class "
            f"positive and explicit-negative support. Feasibility: "
            f"{json.dumps(feasibility, sort_keys=True)}"
        )
    parts = grouped_split(rows, args.seed)
    classes, omitted = eligible_classes(parts)
    print("Pre-training split feasibility: " + json.dumps({
        **feasibility,
        "selected_split_class_support": split_class_support(parts),
        "eligible_classes": classes,
    }, sort_keys=True))
    if not classes:
        raise SystemExit("Training gate: no morph class has the required positive and explicit "
                         "negative support after deterministic grouped split optimization. "
                         f"Feasibility: {json.dumps(feasibility, sort_keys=True)}")

    # Delay heavy imports until the data-quality gates pass.
    import torch
    from PIL import Image
    from torch import nn
    from torch.utils.data import DataLoader, Dataset
    from torchvision import transforms
    from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    normalize = transforms.Normalize(mean=[.485, .456, .406], std=[.229, .224, .225])
    train_transform = transforms.Compose([
        transforms.Resize(256), transforms.RandomResizedCrop(224, scale=(.75, 1.0)),
        transforms.RandomHorizontalFlip(), transforms.ToTensor(), normalize])
    eval_transform = transforms.Compose([
        transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor(), normalize])

    class ImageRows(Dataset):
        def __init__(self, records, transform):
            self.records, self.transform = records, transform

        def __len__(self):
            return len(self.records)

        def __getitem__(self, index):
            row = self.records[index]
            with Image.open(row["image"]) as im:
                image = self.transform(im.convert("RGB"))
            target = torch.tensor([float(row["labels"].get(c, 0)) for c in classes])
            mask = torch.tensor([c in row["labels"] for c in classes], dtype=torch.float32)
            return image, target, mask, row["individual_id"]

    loaders = [DataLoader(ImageRows(part, train_transform if i == 0 else eval_transform),
                          batch_size=args.batch_size, shuffle=(i == 0), num_workers=0)
               for i, part in enumerate(parts)]
    weights = None if args.no_pretrained else MobileNet_V3_Small_Weights.IMAGENET1K_V1
    model = mobilenet_v3_small(weights=weights)
    model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, len(classes))
    model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-4, weight_decay=1e-4)
    criterion = nn.BCEWithLogitsLoss(reduction="none")

    for epoch in range(args.epochs):
        model.train()
        loss_total, batches = 0.0, 0
        for images, targets, masks, _individual_ids in loaders[0]:
            images, targets, masks = images.to(device), targets.to(device), masks.to(device)
            optimizer.zero_grad()
            logits = model(images)
            loss = (criterion(logits, targets) * masks).sum() / masks.sum().clamp(min=1)
            loss.backward()
            optimizer.step()
            loss_total += loss.item()
            batches += 1
        print(f"epoch {epoch + 1}/{args.epochs} masked_bce={loss_total / batches:.4f}")

    def score(loader):
        model.eval()
        true, predicted, individual_ids = ([[] for _ in classes],
                                           [[] for _ in classes],
                                           [[] for _ in classes])
        with torch.inference_mode():
            for images, targets, masks, batch_individual_ids in loader:
                probabilities = model(images.to(device)).sigmoid().cpu()
                for c in range(len(classes)):
                    for i in range(len(images)):
                        if masks[i, c]:
                            true[c].append(int(targets[i, c]))
                            predicted[c].append(float(probabilities[i, c]))
                            individual_ids[c].append(batch_individual_ids[i])
        return true, predicted, individual_ids

    val_true, val_scores, _ = score(loaders[1])
    thresholds = {}
    for idx, key in enumerate(classes):
        thresholds[key] = max((i / 20 for i in range(1, 20)),
                              key=lambda t: (metrics(val_true[idx], val_scores[idx], t)["f1"] or -1, -t))
    test_true, test_scores, test_individual_ids = score(loaders[2])
    test_metrics = {}
    for idx, key in enumerate(classes):
        test_metrics[key] = metrics(test_true[idx], test_scores[idx], thresholds[key])
        test_metrics[key]["bootstrap_95"] = group_bootstrap_intervals(
            test_true[idx], test_scores[idx], test_individual_ids[idx],
            thresholds[key], seed=args.seed + idx)
    macro_f1 = (sum(test_metrics[key]["f1"] for key in classes
                    if test_metrics[key]["f1"] is not None) /
                sum(test_metrics[key]["f1"] is not None for key in classes)
                if any(test_metrics[key]["f1"] is not None for key in classes)
                else None)
    report = {
        "architecture": "torchvision MobileNetV3-Small, independent sigmoid outputs",
        "probability_note": "Raw sigmoid outputs are uncalibrated scores, not confirmed genotype odds.",
        "seed": args.seed, "pretrained_imagenet": not args.no_pretrained,
        "split_images": {k: len(v) for k, v in zip(("train", "validation", "test"), parts)},
        "split_individuals": {k: len({r["individual_id"] for r in v})
                              for k, v in zip(("train", "validation", "test"), parts)},
        "classes": classes, "omitted_classes": omitted,
        "validation_thresholds": thresholds,
        "test_macro_f1": macro_f1,
        "test_macro_f1_bootstrap_95": group_bootstrap_macro_f1(
            test_true, test_scores, test_individual_ids,
            [thresholds[key] for key in classes], seed=args.seed),
        "test_metrics": test_metrics,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.cpu().state_dict(), "classes": classes,
                "thresholds": thresholds, "architecture": "mobilenet_v3_small",
                "image_size": 224}, args.output / "model.pt")
    (args.output / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
