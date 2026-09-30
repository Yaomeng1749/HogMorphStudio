"use strict";
(function installIdentityHelper(target) {
  target.HogMorphReviewIdentity = {
    find(records, index, sha256) {
      const wantedIndex = Number(index);
      return records.find(record => record.index === wantedIndex && record.sha256 === sha256);
    },
    forExport(row, review) {
      return {...review, source_index: row.index, source_sha256: row.sha256,
        visual_triage: row.visual_triage};
    }
  };
})(window);
