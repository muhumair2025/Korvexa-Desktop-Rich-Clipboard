"""
Backup and Migration Service for ClipVault.
Provides complete export and import of clipboard history, pinned clips, file associations,
and image snapshots into portable .zip archives.
"""

from datetime import datetime
import json
import os
from pathlib import Path
import shutil
from typing import Dict, List, Optional, Tuple
import zipfile

from app.constants import APP_NAME, APP_VERSION
from database.repositories import ClipboardRepository
from models.clipboard_file import ClipboardFile
from models.clipboard_item import ClipboardItem
from storage.paths import StoragePaths
from utils.logging_config import get_logger

logger = get_logger("ClipVault.Services.Backup")

BACKUP_MANIFEST_NAME = "manifest.json"
BACKUP_FORMAT_VERSION = "1.0.0"


class BackupService:
    """Handles full export and import of clipboard history and media assets."""

    @classmethod
    def export_backup(
        cls, destination_zip_path: str, repository: ClipboardRepository
    ) -> Tuple[bool, int, str]:
        """
        Exports all clipboard records, associated file metadata, and image files to a zip archive.
        Returns: (success: bool, total_items_exported: int, status_message: str)
        """
        try:
            items = repository.get_items(limit=100000)
            if not items:
                return False, 0, "No clipboard history records found to export."

            dest_path = Path(destination_zip_path)
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Build items manifest
            serialized_items: List[Dict] = []
            image_files_to_pack: List[Tuple[Path, str]] = []  # (src_path, arc_name)

            for item in items:
                item_dict = {
                    "type": item.type,
                    "plain_text": item.plain_text,
                    "html_content": item.html_content,
                    "title": item.title,
                    "preview_text": item.preview_text,
                    "content_hash": item.content_hash,
                    "source_app": item.source_app,
                    "is_pinned": item.is_pinned,
                    "is_sensitive": item.is_sensitive,
                    "use_count": item.use_count,
                    "created_at": item.created_at,
                    "last_used_at": item.last_used_at,
                    "mime_types": item.mime_types,
                    "image_rel_path": None,
                    "thumb_rel_path": None,
                    "files": [],
                }

                # Files metadata
                if item.files:
                    for f in item.files:
                        item_dict["files"].append({
                            "path": f.path,
                            "name": f.name,
                            "size": f.size,
                            "is_dir": f.is_dir,
                        })

                # Media images
                if item.image_path:
                    src_img = Path(item.image_path)
                    if src_img.exists():
                        arc_name = f"media/images/{src_img.name}"
                        item_dict["image_rel_path"] = arc_name
                        image_files_to_pack.append((src_img, arc_name))

                if item.thumbnail_path:
                    src_thumb = Path(item.thumbnail_path)
                    if src_thumb.exists():
                        arc_name = f"media/thumbnails/{src_thumb.name}"
                        item_dict["thumb_rel_path"] = arc_name
                        image_files_to_pack.append((src_thumb, arc_name))

                serialized_items.append(item_dict)

            manifest = {
                "app": APP_NAME,
                "version": APP_VERSION,
                "backup_format_version": BACKUP_FORMAT_VERSION,
                "exported_at": datetime.now().isoformat(),
                "total_items": len(serialized_items),
                "items": serialized_items,
            }

            # Create Zip Archive
            with zipfile.ZipFile(dest_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                # Write manifest
                zipf.writestr(
                    BACKUP_MANIFEST_NAME,
                    json.dumps(manifest, indent=2, ensure_ascii=False),
                )

                # Write media files
                for src_file, arc_name in image_files_to_pack:
                    try:
                        zipf.write(src_file, arc_name)
                    except Exception as e:
                        logger.warning(f"Could not pack image {src_file}: {e}")

            logger.info(f"Successfully exported {len(items)} items to {destination_zip_path}")
            return True, len(items), f"Successfully exported {len(items)} items to backup."

        except Exception as e:
            logger.error(f"Error during backup export: {e}", exc_info=True)
            return False, 0, f"Export failed: {str(e)}"

    @classmethod
    def import_backup(
        cls, source_zip_path: str, repository: ClipboardRepository
    ) -> Tuple[bool, int, str]:
        """
        Restores clipboard records and image files from a backup zip archive.
        Returns: (success: bool, imported_count: int, status_message: str)
        """
        try:
            src_path = Path(source_zip_path)
            if not src_path.exists():
                return False, 0, f"Backup file does not exist: {source_zip_path}"

            if not zipfile.is_zipfile(src_path):
                return False, 0, "Selected file is not a valid zip backup archive."

            with zipfile.ZipFile(src_path, "r") as zipf:
                namelist = zipf.namelist()
                if BACKUP_MANIFEST_NAME not in namelist:
                    return False, 0, "Invalid backup archive: manifest.json is missing."

                manifest_data = zipf.read(BACKUP_MANIFEST_NAME).decode("utf-8")
                manifest = json.loads(manifest_data)

                items_data = manifest.get("items", [])
                if not items_data:
                    return True, 0, "Backup manifest contains 0 items."

                local_img_dir = StoragePaths.get_media_dir()
                local_thumb_dir = StoragePaths.get_thumbnails_dir()
                local_img_dir.mkdir(parents=True, exist_ok=True)
                local_thumb_dir.mkdir(parents=True, exist_ok=True)

                imported_count = 0
                for item_dict in items_data:
                    # Restore media files
                    local_img_path = None
                    if item_dict.get("image_rel_path") and item_dict["image_rel_path"] in namelist:
                        img_filename = Path(item_dict["image_rel_path"]).name
                        target_path = local_img_dir / img_filename
                        with zipf.open(item_dict["image_rel_path"]) as src_img, open(target_path, "wb") as out_img:
                            shutil.copyfileobj(src_img, out_img)
                        local_img_path = str(target_path)

                    local_thumb_path = None
                    if item_dict.get("thumb_rel_path") and item_dict["thumb_rel_path"] in namelist:
                        thumb_filename = Path(item_dict["thumb_rel_path"]).name
                        target_thumb = local_thumb_dir / thumb_filename
                        with zipf.open(item_dict["thumb_rel_path"]) as src_th, open(target_thumb, "wb") as out_th:
                            shutil.copyfileobj(src_th, out_th)
                        local_thumb_path = str(target_thumb)

                    # Restore files list
                    files_list: List[ClipboardFile] = []
                    for f in item_dict.get("files", []):
                        files_list.append(
                            ClipboardFile(
                                path=f["path"],
                                name=f["name"],
                                size=f.get("size", 0),
                                is_dir=f.get("is_dir", 0),
                            )
                        )

                    # Build ClipboardItem
                    item = ClipboardItem(
                        type=item_dict.get("type", "text"),
                        plain_text=item_dict.get("plain_text"),
                        html_content=item_dict.get("html_content"),
                        title=item_dict.get("title"),
                        preview_text=item_dict.get("preview_text"),
                        content_hash=item_dict.get("content_hash"),
                        source_app=item_dict.get("source_app"),
                        image_path=local_img_path,
                        thumbnail_path=local_thumb_path,
                        is_pinned=item_dict.get("is_pinned", 0),
                        is_sensitive=item_dict.get("is_sensitive", 0),
                        use_count=item_dict.get("use_count", 1),
                        created_at=item_dict.get("created_at"),
                        last_used_at=item_dict.get("last_used_at"),
                        mime_types=item_dict.get("mime_types"),
                        files=files_list,
                    )

                    # Insert into repository (handles deduplication or unique insert)
                    if item.content_hash:
                        existing = repository.get_by_hash(item.content_hash)
                        if existing:
                            if item.is_pinned and not existing.is_pinned:
                                repository.toggle_pin(existing.id)
                            continue

                    repository.insert_item(item)
                    imported_count += 1

            logger.info(f"Successfully imported {imported_count} items from {source_zip_path}")
            return True, imported_count, f"Successfully restored {imported_count} items."

        except Exception as e:
            logger.error(f"Error during backup import: {e}", exc_info=True)
            return False, 0, f"Import failed: {str(e)}"
