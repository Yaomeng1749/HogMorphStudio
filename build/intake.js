// Counts only. The supplied photo batch and private previews are not bundled here.
(() => {
    'use strict';
    const zh = new URLSearchParams(location.search).get('lang') === 'zh';
    const copy = zh ? {
        eyebrow: '新增本地照片批次', title: '新照片进入复核',
        description: '新增文件已在本地完成初筛。目视候选不等于经过核验的形态样本，也不能直接用于模型训练。',
        screened: '可解码图片', candidates: '疑似猪鼻蛇照片', eligible: '满足训练门槛', link: '查看清点报告 ↗'
    } : {
        eyebrow: 'NEW LOCAL BATCH', title: 'More photos, now in review',
        description: 'A new unlabelled folder was screened locally. Visual candidates are not verified morph examples or training data.',
        screened: 'images screened', candidates: 'possible hognose photos', eligible: 'training ready', link: 'Read the intake audit ↗'
    };
    const $ = (id) => document.getElementById(id);
    fetch('data/incoming_summary.json').then((response) => {
        if (!response.ok)
            throw new Error('intake summary unavailable');
        return response.json();
    }).then((summary) => {
        const removed = summary.status === 'candidate_batch_removed_by_owner';
        if (!removed && summary.status?.startsWith('local visual intake') !== true)
            return;
        if (removed)
            return;
        $('incoming-eyebrow').textContent = copy.eyebrow;
        $('incoming-title').textContent = copy.title;
        $('incoming-description').textContent = copy.description;
        $('incoming-screened-label').textContent = copy.screened;
        $('incoming-candidates-label').textContent = copy.candidates;
        $('incoming-eligible-label').textContent = copy.eligible;
        $('incoming-audit-link').textContent = copy.link;
        $('incoming-screened').textContent = summary.decoded_images;
        $('incoming-candidates').textContent = summary.visually_plausible_captive_western_hognose;
        $('incoming-eligible').textContent = summary.eligible_morph_training_images;
        $('incoming').hidden = false;
    }).catch(() => { });
})();
export {};
