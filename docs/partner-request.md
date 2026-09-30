# Breeder contribution request / 繁育者数据合作邀请

## Short message (English)

Hello, I am developing HogMorph Studio for a U.S. hackathon. It is an educational Western Hognose photo and phenotype research tool. I am looking for breeder-contributed, individually identified photos to build and evaluate a small visual phenotype model. Would you be open to discussing a contribution of your own photographs and records?

For each animal, I would request its unique ID, the original photos, visible trait names, any breeding or genetic evidence you are comfortable sharing, and the photographer's credit. I would ask separately for written permission covering: (1) local model training and evaluation, (2) display in the hackathon demo, and (3) redistribution or public display of the original photos in a public repository/site. Please specify whether any permission is non-commercial, attribution-required, revocable, or limited to a particular event or period. I will distinguish your stated genetics from visual predictions and credit you as requested. Participation is voluntary; I will not copy your Instagram or MorphMarket photographs without your permission.

If you are interested, I can send a short data and permission form. Thank you.

## 中文说明

这封英文消息用于向繁育者征集**由其拥有使用权的原始照片**和按蛇只区分的资料。需要分别确认：模型训练与评估许可、比赛现场展示许可、以及原图能否在公开仓库/网页展示或再分发；同时确认是否非商业、署名要求、许可期限和撤回方式。项目代码采用 MIT 不会自动把照片也变成 MIT；照片必须由权利人另行授权并保留自己的许可和署名。

## Contribution form fields

| Field | Purpose |
|---|---|
| Breeder and photographer name | Attribution and rights holder |
| Unique animal ID and birth/hatch record | Keep one animal out of both train and test |
| Original photo files and capture dates | Track source and avoid duplicates |
| Visible trait claims | Candidate phenotype labels |
| Confirmed genotype / possible het / unknown | Separate visible and non-visible claims |
| Breeding or genetic evidence URL/file | Review the claim |
| Training and evaluation permission | Define model-use scope |
| Hackathon demo display permission | Define event-use scope |
| Public web display and source-image redistribution permission | Distinguish embedding/hosting from downstream reuse |
| Model-weight and output publication scope | Confirm whether trained weights, derived artifacts, and evaluation results may be published, and under what terms |
| Permission duration and withdrawal process | Record expiry, revocation contact, and what happens to existing derived artifacts |
| Credit text and withdrawal contact | Attribution and later corrections |

The contribution form is a proposed workflow, not permission already obtained. No message has been sent.

## Minimum collection target for an evaluated trait

The prototype's identity-level 70/15/15 split has a capacity floor of 39 distinct snakes and 100 eligible photos overall. For any one trait to pass the current support gate, it also needs at least 11 distinct positive individuals and 11 distinct individuals with explicit, evidence-supported negatives: 5 of each in training and 3 of each in validation and test. These per-trait individuals may overlap with other traits' cohorts, but all photos of a given snake must stay in one split. Unsupported traits will be omitted from evaluation rather than filled with unknown labels or assumed negatives. These are gate minima, not a claim that the dataset will be statistically adequate.
