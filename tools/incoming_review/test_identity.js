"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const browser = {window: {}};
vm.runInNewContext(fs.readFileSync(`${__dirname}/identity.js`, "utf8"), browser);
const identity = browser.window.HogMorphReviewIdentity;
const sharedSha = "a".repeat(64);
const duplicateRows = [
  {index: 17, sha256: sharedSha, visual_triage: "candidate_western_hognose"},
  {index: 18, sha256: sharedSha, visual_triage: "uncertain"}
];

const clicked = identity.find(duplicateRows, "18", sharedSha);
assert.equal(clicked.index, 18, "list click resolves the clicked index despite a duplicate SHA");
assert.equal(clicked.visual_triage, "uncertain");

const sharedReview = {source_index: 17, source_sha256: sharedSha, notes: "shared SHA-keyed review"};
const exported = identity.forExport(clicked, sharedReview);
assert.equal(exported.source_index, 18, "export identity comes from the row, not stored review data");
assert.equal(exported.source_sha256, sharedSha);
assert.equal(exported.visual_triage, "uncertain");
assert.equal(sharedReview.source_index, 17, "export remapping does not mutate the shared review object");

const restored = identity.find(duplicateRows, 18, sharedSha);
assert.equal(restored.index, 18, "restore selection uses the same index plus SHA identity");
console.log("duplicate SHA queue/export identity checks passed");
