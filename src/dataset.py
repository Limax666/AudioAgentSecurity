import os
import json
import logging
from config import METADATA_FILENAME

logger = logging.getLogger(__name__)

class AttackDataset:
    TYPE_MAP = {
        "type1": 1,
        "type2": 2,
        "type3": 3
    }

    def __init__(self, data_dir, dataset_type="type1", attack_method="all"):
        self.data_dir = data_dir
        self.dataset_type = dataset_type
        self.attack_method = attack_method
        self.data = self._load_data()

    def _load_data(self):
        """
        Load and filter the dataset based on metadata.json.
        Supports both v4 (filename, attack_method) and v5 (mixed_path, method) formats.
        """
        metadata_path = os.path.join(self.data_dir, METADATA_FILENAME)
        if not os.path.exists(metadata_path):
            logger.error(f"Metadata file not found at {metadata_path}")
            return []

        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse metadata JSON: {e}")
            return []

        # Map IDs for legacy version type1/2/3
        target_type_id = self.TYPE_MAP.get(self.dataset_type.lower())
        
        # Build ID -> benign text mapping, used for v4 type1 fallback logic (legacy logic)
        type2_benign_text_map = {}
        for entry in metadata:
            if entry.get('injection_type') == 2:
                type2_benign_text_map[entry.get('id')] = entry.get('benign_text', "")

        dataset = []
        for entry in metadata:
            # 1. Determine attack method
            # v5 uses 'method', v4 uses 'attack_method'
            entry_method = entry.get('method') or entry.get('attack_method')
            
            # 2. Determine audio path
            # v5 uses 'mixed_path', v4 uses 'filename'. The physical distance
            # benchmark uses 'output_path'.
            rel_path = entry.get('mixed_path') or entry.get('filename') or entry.get('output_path')
            if not rel_path:
                continue # Skip if path not found

            # 3. Filter injection type (legacy only)
            # If dataset_type is a specific type (type1/2/3), filter accordingly.
            # If it's 'mixed' or v5 format without injection_type, skip this check.
            if target_type_id is not None:
                if entry.get('injection_type') != target_type_id:
                    continue

            # 4. Filter attack method
            if self.attack_method != "all" and entry_method != self.attack_method:
                continue

            # Build full path
            audio_path = os.path.join(self.data_dir, rel_path)
            
            # 5. Determine original/benign text
            # v5 explicitly includes 'benign_text' field.
            # v4 Type 1 logic: use Type 2's benign text.
            benign_text = entry.get('benign_text', "")
            
            inj_type = entry.get('injection_type')
            if inj_type == 1 and not benign_text:
                # v4 Type 1 fallback logic
                benign_text = type2_benign_text_map.get(entry.get('id'), "")
                if not benign_text:
                     benign_text = entry.get('malicious_text', "")
            
            # If benign text is still missing, use malicious text as original text (e.g., edge cases)
            original_text = benign_text if benign_text else entry.get('malicious_text', "")

            dataset.append({
                "id": entry.get('id', 'unknown'),
                "audio_path": audio_path,
                "original_text": original_text,
                "benign_text": original_text,
                "malicious_text": entry.get('malicious_text', ""),
                "attack_type": entry_method or 'unknown',
                "injection_type": inj_type,
                "severity": entry.get('severity', 1),
                "injection_strategy": entry.get('injection_strategy'),
                "offset_seconds": entry.get('offset_seconds'),
                "overlap_ratio": entry.get('overlap_ratio'),
                "snr": entry.get('snr')
            })

        return dataset

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]
