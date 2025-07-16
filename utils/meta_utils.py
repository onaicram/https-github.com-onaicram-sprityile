import json
import os
from datetime import datetime
from utils.controls_utils import is_atlas_file


class MetaUtils:
    
    @staticmethod
    def get_meta_path(image_path: str) -> str:
        return image_path + ".meta.json"

    @staticmethod
    def save_meta(image_path, tile_size, editable=True, cols=None, rows=None, start_tile=None, end_tile=None):
        meta_path = MetaUtils.get_meta_path(image_path)
        existing = {}

        # Carica meta precedente se esiste
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception as e:
                print(f"[MetaUtils] Errore lettura meta esistente: {e}")

        # Dati base
        data = {
            "tile_size": tile_size,
            "editable": editable,
            "created_at": existing.get("created_at", datetime.now().isoformat())
        }

        is_atlas = is_atlas_file(image_path)

        if is_atlas:
            data["cols"] = cols if cols is not None else existing.get("cols", 10)
            data["rows"] = rows if rows is not None else existing.get("rows", 10)
            data["start_tile"] = start_tile if start_tile is not None else existing.get("start_tile", [0, 0])
            data["end_tile"] = end_tile if end_tile is not None else existing.get("end_tile", [0, 0])

        try:
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[MetaUtils] Errore salvataggio meta: {e}")

    @staticmethod
    def load_meta(image_path):
        meta_path = MetaUtils.get_meta_path(image_path)
        if not os.path.exists(meta_path):
            return None
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[MetaUtils] Errore lettura meta: {e}")
            return None
