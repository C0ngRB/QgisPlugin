import json
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.registry.algorithms import ACCESSIBILITY_PROVIDER_ID, TERRAIN_HYDRO_PROVIDER_ID, provider_algorithms

PLUGIN_IDS = (ACCESSIBILITY_PROVIDER_ID, TERRAIN_HYDRO_PROVIDER_ID)
REQUIRED_PLUGIN_FILES = ("metadata.txt", "__init__.py", "plugin.py", "provider.py", "README.md", "LICENSE")


def repo_root():
    """函数含义：定位项目根目录；上游由构建入口和测试调用；下游提供 core、plugins、build、dist 的统一基准路径；风险点是脚本移动位置后需要同步调整。"""
    return ROOT_DIR


def reset_directory(path):
    """函数含义：清空并重建构建目录；上游由 build_all 调用；下游保证 build/dist 由脚本生成而非手工维护；风险点是 Windows 删除目录时可能遇到文件已被并发清理。"""
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)


def validate_plugin_source(plugin_dir):
    """函数含义：校验插件源码必需文件；上游由 stage_plugin 调用；下游阻止缺少元数据或文档的 zip 进入 dist；风险点是只校验文件存在不校验 QGIS 运行时行为。"""
    missing_files = [file_name for file_name in REQUIRED_PLUGIN_FILES if not (plugin_dir / file_name).exists()]
    if missing_files:
        raise FileNotFoundError(f"{plugin_dir.name} 缺少必需文件: {', '.join(missing_files)}")


def stage_plugin(root_dir, plugin_id, build_dir):
    """函数含义：把单个插件源码和共享 core 复制到发布态目录；上游由 build_all 调用；下游生成 zip 待压缩内容；风险点是复制结果必须保持 QGIS 插件根目录结构。"""
    source_dir = root_dir / "plugins" / plugin_id
    validate_plugin_source(source_dir)

    staged_plugin_dir = build_dir / plugin_id / plugin_id
    ignore_cache = shutil.ignore_patterns("__pycache__", "*.pyc")
    shutil.copytree(source_dir, staged_plugin_dir, ignore=ignore_cache)
    shutil.copytree(root_dir / "core", staged_plugin_dir / "core", ignore=ignore_cache)
    return staged_plugin_dir


def zip_plugin(staged_plugin_dir, dist_dir):
    """函数含义：压缩单个已暂存插件目录；上游由 build_all 调用；下游生成 QGIS 可安装 zip；风险点是 zip 内必须以插件目录作为根路径。"""
    zip_path = dist_dir / f"{staged_plugin_dir.name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in staged_plugin_dir.rglob("*"):
            if file_path.is_file():
                zip_file.write(file_path, file_path.relative_to(staged_plugin_dir.parent))
    return zip_path


def write_manifest(dist_dir, zip_paths):
    """函数含义：写入发布清单；上游由 build_all 调用；下游记录插件 zip、算法 ID 和构建时间；风险点是清单必须与实际 zip 同步生成。"""
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "plugins": [
            {
                "plugin_id": plugin_id,
                "zip": str(zip_paths[plugin_id].name),
                "algorithms": [f"{plugin_id}:{name}" for name in provider_algorithms(plugin_id)],
            }
            for plugin_id in PLUGIN_IDS
        ],
    }
    manifest_path = dist_dir / "release_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as manifest_file:
        json.dump(manifest, manifest_file, ensure_ascii=False, indent=2)
    return manifest_path


def write_build_report(dist_dir, zip_paths, manifest_path):
    """函数含义：写入人类可读构建报告；上游由 build_all 调用；下游给课程交付和 Codex 复查使用；风险点是报告只描述构建结果不替代测试。"""
    lines = ["WUDA QGIS plugins build report", ""]
    for plugin_id, zip_path in zip_paths.items():
        lines.append(f"- {plugin_id}: {zip_path.name}")
    lines.append(f"- manifest: {manifest_path.name}")
    report_path = dist_dir / "build_report.txt"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def build_all():
    """函数含义：执行完整插件构建；上游由命令行和测试调用；下游生成 build 目录、两个 zip、manifest 和 report；风险点是会重建 build/dist 产物目录。"""
    root_dir = repo_root()
    build_dir = root_dir / "build"
    dist_dir = root_dir / "dist"
    reset_directory(build_dir)
    reset_directory(dist_dir)

    zip_paths = {}
    for plugin_id in PLUGIN_IDS:
        staged_plugin_dir = stage_plugin(root_dir, plugin_id, build_dir)
        zip_paths[plugin_id] = zip_plugin(staged_plugin_dir, dist_dir)

    manifest_path = write_manifest(dist_dir, zip_paths)
    report_path = write_build_report(dist_dir, zip_paths, manifest_path)
    return {"zip_paths": zip_paths, "manifest_path": manifest_path, "report_path": report_path}


if __name__ == "__main__":
    build_all()
