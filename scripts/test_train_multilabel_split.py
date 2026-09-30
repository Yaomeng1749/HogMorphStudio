import unittest

from train_multilabel import (
    eligible_classes,
    group_bootstrap_intervals,
    group_bootstrap_macro_f1,
    grouped_split,
    metrics,
    split_feasibility,
    validate_individual_labels,
)


def synthetic_rows(positive_count=11, negative_count=11, unknown_count=17):
    rows = []
    for index in range(positive_count):
        rows.append({"id": f"p{index}", "individual_id": f"p{index}",
                     "labels": {"morph:expressed": 1}})
    for index in range(negative_count):
        rows.append({"id": f"n{index}", "individual_id": f"n{index}",
                     "labels": {"morph:expressed": 0}})
    for index in range(unknown_count):
        rows.append({"id": f"u{index}", "individual_id": f"u{index}",
                     "labels": {}})
    return rows


class GroupedSplitTests(unittest.TestCase):
    def test_seeded_split_is_repeatable_and_keeps_individuals_together(self):
        rows = synthetic_rows()
        first = grouped_split(rows, seed=19)
        second = grouped_split(rows, seed=19)
        self.assertEqual(first, second)
        self.assertEqual([len({r["individual_id"] for r in p}) for p in first], [27, 6, 6])
        locations = {}
        for split_index, part in enumerate(first):
            for row in part:
                locations.setdefault(row["individual_id"], set()).add(split_index)
        self.assertTrue(all(len(splits) == 1 for splits in locations.values()))

    def test_optimizer_finds_feasible_class_at_39_distinct_individuals(self):
        parts = grouped_split(synthetic_rows(), seed=42)
        classes, omitted = eligible_classes(parts)
        self.assertEqual(classes, ["morph:expressed"])
        self.assertEqual(omitted, {})

    def test_reports_30_individual_split_capacity_as_impossible(self):
        report = split_feasibility(synthetic_rows(positive_count=11, negative_count=11,
                                                  unknown_count=8))
        self.assertEqual(report["individuals"], 30)
        self.assertEqual(report["partition_individuals"],
                         {"train": 21, "validation": 4, "test": 5})
        self.assertEqual(report["minimum_individuals_for_split_capacity"], 39)
        self.assertFalse(report["classes"]["morph:expressed"]["possible_by_global_counts"])

    def test_conflicting_labels_for_same_individual_are_rejected(self):
        rows = [
            {"id": "view-1", "individual_id": "snake-a", "labels": {"morph": 1}},
            {"id": "view-2", "individual_id": "snake-a", "labels": {"morph": 0}},
        ]
        with self.assertRaisesRegex(ValueError, "Contradictory explicit labels"):
            validate_individual_labels(rows)

    def test_bootstrap_resamples_individual_groups_deterministically(self):
        ids = ["snake-a", "snake-a", "snake-b", "snake-b",
               "snake-c", "snake-c", "snake-d", "snake-d"]
        truth = [1, 1, 0, 0, 1, 1, 0, 0]
        scores = [.9, .8, .2, .1, .7, .6, .4, .3]
        first = group_bootstrap_intervals(truth, scores, ids, .5,
                                          seed=7, iterations=100)
        second = group_bootstrap_intervals(truth, scores, ids, .5,
                                           seed=7, iterations=100)
        self.assertEqual(first, second)
        self.assertEqual(first["individuals"], 4)
        self.assertEqual(first["resampling_unit"], "individual_id")
        self.assertIn("average_precision", first["intervals_95"])
        self.assertIn("f1", first["intervals_95"])
        self.assertEqual(metrics(truth, scores, .5)["average_precision"], 1.0)

    def test_average_precision_groups_tied_scores_independent_of_row_order(self):
        first = metrics([1, 0], [.5, .5], threshold=.5)["average_precision"]
        reversed_rows = metrics([0, 1], [.5, .5], threshold=.5)["average_precision"]
        self.assertEqual(first, .5)
        self.assertEqual(reversed_rows, .5)

        labels = [1, 0, 1, 0]
        scores = [.9, .5, .5, .1]
        original_ap = metrics(labels, scores, threshold=.5)["average_precision"]
        reordered_ap = metrics([0, 1, 0, 1], [.1, .5, .5, .9],
                               threshold=.5)["average_precision"]
        self.assertEqual(original_ap, reordered_ap)

    def test_threshold_recall_remains_zero_and_partial_after_ap_calculation(self):
        zero = metrics([1, 1, 0, 0], [.4, .3, .2, .1], .5)
        partial = metrics([1, 1, 0, 0], [.9, .4, .8, .1], .5)
        self.assertEqual(zero["recall"], 0.0)
        self.assertEqual(partial["recall"], 0.5)

    def test_bootstrap_reports_valid_counts_and_complete_class_policy(self):
        per_class = group_bootstrap_intervals(
            [1, 0], [.8, .2], ["positive", "negative"], .5,
            seed=3, iterations=100)
        self.assertEqual(per_class["iterations"], 100)
        self.assertLess(per_class["valid_iterations"]["f1"], 100)
        self.assertEqual(per_class["valid_iterations"]["f1"],
                         per_class["valid_iterations"]["average_precision"])
        self.assertIn("only resamples where that metric is defined",
                      per_class["conditioning_policy"])

        ids = ["a", "b", "c", "d"]
        truths = [[1, 1, 0, 0], [1, 0, 1, 0]]
        scores = [[.9, .8, .2, .1], [.9, .2, .8, .1]]
        macro = group_bootstrap_macro_f1(
            truths, scores, [ids, ids], [.5, .5], seed=11, iterations=100)
        self.assertGreater(macro["valid_iterations"], 0)
        self.assertLess(macro["valid_iterations"], macro["iterations"])
        self.assertIn("every evaluated class", macro["conditioning_policy"])

    def test_bootstrap_returns_none_interval_when_no_resample_is_valid(self):
        report = group_bootstrap_intervals(
            [1, 0], [.9, .1], ["positive", "negative"], .5,
            seed=0, iterations=1)
        self.assertEqual(report["iterations"], 1)
        self.assertEqual(report["valid_iterations"], {
            "precision": 0, "recall": 0, "f1": 0, "average_precision": 0})
        self.assertEqual(report["intervals_95"], {
            "precision": None, "recall": None, "f1": None,
            "average_precision": None})


if __name__ == "__main__":
    unittest.main()
