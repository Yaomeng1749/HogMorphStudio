// Field observations are species-only references, never morph examples or negatives.
(() => {
    'use strict';
    const zh = new URLSearchParams(location.search).get('lang') === 'zh';
    const copy = zh ? {
        eyebrow: '物种参考', title: '少量野外观察照片',
        description: '这些有明确许可的野外照片展示西部猪鼻蛇的自然外观差异。它们没有经过核验的形态或基因型标签，也不参与形态匹配和训练。',
        note: '每张照片均链接至来源及对应许可。“看起来是野生原色”不能证明它没有形态基因。',
        observation: '观察记录', license: '照片许可', unavailable: '野外参考照片暂时无法载入。'
    } : {
        eyebrow: 'SPECIES REFERENCE', title: 'A small wild reference set',
        description: 'Licensed field observations show natural variation in Western Hognoses. They have no verified morph or genotype labels and are excluded from the morph matcher and training set.',
        note: 'Each photo links to its source and individual license. “Wild type appearance” is not a proven absence of morph genes.',
        observation: 'Observation', license: 'Photo license', unavailable: 'Wild reference photos are temporarily unavailable.'
    };
    const $ = (id) => document.getElementById(id);
    $('wild-eyebrow').textContent = copy.eyebrow;
    $('wild-title').textContent = copy.title;
    $('wild-description').textContent = copy.description;
    $('wild-license-note').textContent = copy.note;
    fetch('data/species_manifest.json').then((response) => {
        if (!response.ok)
            throw new Error('manifest unavailable');
        return response.json();
    }).then((manifest) => {
        if (manifest.scope !== 'species_only' || manifest.morph_training_eligible !== false)
            throw new Error('scope mismatch');
        const photos = Array.isArray(manifest.photos) ? manifest.photos : [];
        $('wild-count').textContent = String(photos.length).padStart(2, '0');
        const gallery = $('wild-gallery');
        for (const photo of photos) {
            if (photo.scope !== 'species_only' || photo.eligible_for_morph_training !== false)
                continue;
            const card = document.createElement('article');
            card.className = 'wild-card';
            const image = document.createElement('img');
            image.loading = 'lazy';
            image.src = photo.file;
            image.alt = zh ? `西部猪鼻蛇野外观察 ${photo.observation_id}` : `Western Hognose field observation ${photo.observation_id}`;
            const details = document.createElement('div');
            details.className = 'wild-card-details';
            const id = document.createElement('span');
            id.textContent = `${copy.observation} #${photo.observation_id}`;
            const credit = document.createElement('small');
            credit.textContent = photo.license === 'cc0' ? `iNaturalist · ${photo.observer_login} · CC0` : photo.attribution;
            const links = document.createElement('div');
            links.className = 'wild-card-links';
            for (const [label, url] of [[zh ? '原图 ↗' : 'Source ↗', photo.photo_page], [copy.license + ' ↗', photo.license_url]]) {
                const link = document.createElement('a');
                link.href = url;
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
                link.textContent = label;
                links.append(link);
            }
            details.append(id, credit, links);
            card.append(image, details);
            gallery.append(card);
        }
    }).catch((error) => {
        console.warn('Species reference unavailable:', error);
        $('wild-gallery').textContent = copy.unavailable;
    });
    const captiveCopy = zh ? {
        eyebrow: '圈养物种参考', title: '已许可的圈养照片',
        description: '这些开放许可照片被 iNaturalist 观察者标记为圈养。它们没有核实过的形态标签或蛇只身份，不参与形态分析和训练。',
        note: '每张图链接至原始观察记录和单张照片许可，并说明了图片处理。同一观察记录中的多张图可能是同一只未核验个体。',
        modified: '图片处理：采用 iNaturalist 中尺寸衍生图，校正方向、转为 JPEG 并移除嵌入元数据。',
        unavailable: '圈养参考照片暂时无法载入。'
    } : {
        eyebrow: 'CAPTIVE SPECIES REFERENCE', title: 'Licensed captive references',
        description: 'These openly licensed photos are marked captive by iNaturalist observers. They have no verified morph labels or animal identities and do not enter morph analysis or training.',
        note: 'Each card links to its photo, observation record, and individual license, and states how the image was modified. Several photos may show one unverified individual.',
        modified: 'Modified: iNaturalist medium-sized derivative; orientation corrected, converted to JPEG, and embedded metadata removed.',
        unavailable: 'Captive reference photos are temporarily unavailable.'
    };
    $('captive-eyebrow').textContent = captiveCopy.eyebrow;
    $('captive-title').textContent = captiveCopy.title;
    $('captive-description').textContent = captiveCopy.description;
    $('captive-license-note').textContent = captiveCopy.note;
    fetch('data/captive_species_manifest.json').then((response) => {
        if (!response.ok)
            throw new Error('captive manifest unavailable');
        return response.json();
    }).then((manifest) => {
        if (manifest.scope !== 'species_only' || manifest.subscope !== 'captive_unlabeled_reference_only' || manifest.morph_training_eligible !== false) {
            throw new Error('captive reference scope mismatch');
        }
        const photos = Array.isArray(manifest.photos) ? manifest.photos : [];
        $('captive-count').textContent = String(photos.length).padStart(2, '0');
        const gallery = $('captive-gallery');
        for (const photo of photos) {
            if (photo.scope !== 'captive_species_only_reference' || photo.eligible_for_morph_training !== false || photo.captive !== true)
                continue;
            const card = document.createElement('article');
            card.className = 'wild-card';
            const image = document.createElement('img');
            image.loading = 'lazy';
            image.src = photo.file;
            image.alt = zh ? `圈养西部猪鼻蛇参考照片 ${photo.photo_id}` : `Captive Western Hognose reference photo ${photo.photo_id}`;
            const details = document.createElement('div');
            details.className = 'wild-card-details';
            const id = document.createElement('span');
            id.textContent = `${copy.observation} #${photo.observation_id} · Photo ${photo.photo_id}`;
            const credit = document.createElement('small');
            credit.textContent = photo.license_code === 'cc0' ? `iNaturalist · ${photo.observer_login} · CC0` : photo.attribution;
            const modification = document.createElement('small');
            modification.textContent = captiveCopy.modified;
            const links = document.createElement('div');
            links.className = 'wild-card-links';
            const sourceLabel = zh ? '原图 ↗' : 'Photo ↗';
            const observationLabel = zh ? '观察记录 ↗' : 'Observation ↗';
            for (const [label, url] of [[sourceLabel, photo.photo_page], [observationLabel, photo.observation_page], [copy.license + ' ↗', photo.license_url]]) {
                const link = document.createElement('a');
                link.href = url;
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
                link.textContent = label;
                links.append(link);
            }
            details.append(id, credit, modification, links);
            card.append(image, details);
            gallery.append(card);
        }
    }).catch((error) => {
        console.warn('Captive species reference unavailable:', error);
        $('captive-gallery').textContent = captiveCopy.unavailable;
    });
})();
export {};
