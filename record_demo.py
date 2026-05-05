# -*- coding: utf-8 -*-
# QScheduler AI - X demo video recorder
# Playwright -> WebM -> MP4

import asyncio
import os
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

OUTPUT_DIR = Path(__file__).parent / "video_output"
OUTPUT_DIR.mkdir(exist_ok=True)

WEBM_PATH = OUTPUT_DIR / "demo_raw.webm"
MP4_PATH  = OUTPUT_DIR / "qscheduler_demo.mp4"
APP_URL   = "https://manufacturing-scheduler-production.up.railway.app"


async def record():
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(OUTPUT_DIR),
            record_video_size={"width": 1280, "height": 720},
            device_scale_factor=1,
        )
        page = await context.new_page()

        print("[1] Opening app...")
        await page.goto(APP_URL)

        # Dashboard - KPI counters animate
        print("[2] Dashboard - 75%ズーム適用")
        await page.wait_for_timeout(1500)   # 初期レンダリング待機
        # 75%ズームで画面下部を見切れなくする
        await page.evaluate("document.body.style.zoom = '0.75'")
        await page.wait_for_timeout(1000)

        # AI Forecast tab
        print("[3] Click AI Forecast tab")
        await page.click("text=AI需要予測")
        await page.wait_for_timeout(600)

        # Re-analyze button
        print("[4] Click re-analyze (2.8s)")
        await page.click("#fc-btn")
        await page.wait_for_timeout(2900)

        # Production Schedule tab
        print("[5] Click Schedule tab")
        await page.click("text=生産スケジュール")
        await page.wait_for_timeout(600)

        # AI optimization
        print("[6] Click AI Optimize (~4s)")
        await page.click("#opt-btn")
        await page.wait_for_timeout(4200)

        # Final hold
        print("[7] Final hold (1s)")
        await page.wait_for_timeout(1000)

        await context.close()
        await browser.close()

    # Playwright が保存した webm ファイルを探す
    webm_files = sorted(OUTPUT_DIR.glob("*.webm"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not webm_files:
        print("ERROR: WebM file not found")
        sys.exit(1)
    latest_webm = webm_files[0]
    WEBM_PATH.unlink(missing_ok=True)  # 既存ファイルを先に削除（Windows対応）
    latest_webm.rename(WEBM_PATH)
    print(f"OK WebM saved: {WEBM_PATH}")


def convert_to_mp4():
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"Converting to MP4...")
    cmd = [
        ffmpeg,
        "-y",
        "-i", str(WEBM_PATH),
        # 映像: H.264, CRF=18 (高品質)
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "slow",
        "-profile:v", "high",
        "-pix_fmt", "yuv420p",
        # 音声なし
        "-an",
        # SNS 向け: faststart (ストリーミング対応)
        "-movflags", "+faststart",
        str(MP4_PATH),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("ERROR: ffmpeg failed")
        print(result.stderr)
        sys.exit(1)
    size_mb = MP4_PATH.stat().st_size / 1024 / 1024
    print(f"OK MP4 saved: {MP4_PATH}")
    print(f"   Size: {size_mb:.1f} MB")


async def main():
    print("=" * 50)
    print("QScheduler AI - Demo Video Recorder")
    print("=" * 50)
    await record()
    convert_to_mp4()
    print()
    print("=" * 50)
    print(f"DONE: {MP4_PATH.resolve()}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
