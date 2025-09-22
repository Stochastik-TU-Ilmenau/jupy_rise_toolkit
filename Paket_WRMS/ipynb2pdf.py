import os
import sys
from glob import glob
from natsort import natsorted
from pypdf import PdfWriter


# pdf formatting options
pdf_params = {
    # see: https://playwright.dev/docs/api/class-page#page-pdf
    "format": 'A4',
    "scale": 0.7,
    "landscape": False,
    "print_background": True,
    "margin": {
        "top": "0",
        "right": "0",
        "bottom": "0",
        "left": "0",
        },
}

# to correctly display latex formulas we have to wait for mathjax to finish
# TODO: wait for a specific event and not for a fixed amount of time?
wait_for_mathjax_timeout = 10000 # ms

# file name of merged pdf
output_filename = 'StochMath.pdf'

# custom bookmarks (if None file names are used)
# should be a list (of strings) of length equal to the number of merged pdfs
custom_bookmarks = [
    "1 Daten",
    "2 Deskriptive Statistik",
    "3 Multivariate Daten",
    "4 Diskrete Wahrscheinlichkeitsräume",
    "5 Abhängigkeit und Unabhängigkeit",
    "6 Eigenschaften von Verteilungen",
    "7 Gesetze der großen und kleinen Zahlen",
    "8 Schätzen",
    ]


def main(arg = sys.argv[1:]):
    """
    Script converts all ipynb files in current directory to html (1.) and then to pdf (2.).
    The pdf files are merged (3.) into one pdf file with bookmarks.

    run complete workflow:
        python ipynb2pdf.py
    the same as:
        python ipynb2pdf.py -html -pdf -merge
    
    create only html files:
        python ipynb2pdf.py -html
    
    create only pdf files (needs html files):
        python ipynb2pdf.py -pdf
    
    only merge pdf files:
        python ipynb2pdf.py -merge
    
    create pdf files and merge:
        python ipynb2pdf.py -pdf -merge
    """

    # 1. convert all jupyter notebooks to html with nbconvert:
    if '-html' in arg or not arg:
        for root, dirs, files in os.walk( os.getcwd() ):
            # select file name
            for file in files:
                # check the extension of files
                if file.endswith('.ipynb'):
                    #windows-stuff
                    os.system('python -m nbconvert --to html --no-input ' + os.path.basename( file ) )

        #os.system('jupyter nbconvert --to html *.ipynb --no-input')


    # 2. convert html files to pdf with playwright (using chromium):
    if '-pdf' in arg or not arg:
        html_files = glob('*.html') # lists all html files in current directory
        
        # filter files (optional)
        #html_files = [h for h in html_files if '_U_' not in h] # remove "Uebung"

        for html_file in html_files:
            print('converting to pdf:', html_file)
                
            with open(html_file, "r", encoding='utf-8') as f:
                html = f.read()

            pdf_data = run_playwright(html, pdf_params=pdf_params, timeout=wait_for_mathjax_timeout)

            with open(html_file + '.pdf', "wb") as f:
                f.write(pdf_data)


    # 3. merge pdfs and create bookmarks:
    if '-merge' in arg or not arg:
        pdf_files = natsorted(glob('*.html.pdf')) # here the order is important!

        file_names = [f.split('.html.pdf')[0] for f in pdf_files]
        bookmarks = custom_bookmarks if custom_bookmarks else file_names

        merger = PdfWriter()
        for pdf_file, bookmark in zip(pdf_files, bookmarks):
            if pdf_file == output_filename:
                continue
            print("appending:", pdf_file)
            merger.append(pdf_file, bookmark)
        merger.write(output_filename)
        merger.close()











################################################################################################
# 'run_playwright' function copied from nbconvert webpdf exporter:

"""Export to PDF via a headless browser"""

import asyncio
import concurrent.futures
import subprocess
import tempfile
from importlib import util as importlib_util
from traitlets import Bool

PLAYWRIGHT_INSTALLED = importlib_util.find_spec("playwright") is not None
IS_WINDOWS = os.name == "nt"

allow_chromium_download = Bool(
    False,
    help="Whether to allow downloading Chromium if no suitable version is found on the system.",
).tag(config=True)

disable_sandbox = Bool(
    False,
    help="""
    Disable chromium security sandbox when converting to PDF.
    This is required for webpdf to work inside most container environments.
    """,
).tag(config=True)


def run_playwright(html, pdf_params={}, timeout=3000):
    """Run playwright."""

    async def main(temp_file):
        """Run main playwright script."""
        args = ["--no-sandbox"] if disable_sandbox else []
        try:
            from playwright.async_api import async_playwright  # type: ignore[import-not-found]
        except ModuleNotFoundError as e:
            msg = (
                "Playwright is not installed to support Web PDF conversion. "
                "Please install `nbconvert[webpdf]` to enable."
            )
            raise RuntimeError(msg) from e

        if allow_chromium_download:
            cmd = [sys.executable, "-m", "playwright", "install", "chromium"]
            subprocess.check_call(cmd)  # noqa

        playwright = await async_playwright().start()
        chromium = playwright.chromium

        try:
            browser = await chromium.launch(
                handle_sigint=False, handle_sigterm=False, handle_sighup=False, args=args
            )
        except Exception as e:
            msg = (
                "No suitable chromium executable found on the system. "
                "Please use '--allow-chromium-download' to allow downloading one,"
                "or install it using `playwright install chromium`."
            )
            raise RuntimeError(msg) from e

        page = await browser.new_page()
        await page.emulate_media(media="print")
        await page.wait_for_timeout(100) # orig. 100 ms
        await page.goto(f"file://{temp_file.name}", wait_until="networkidle")
        await page.wait_for_timeout(timeout) # orig. 100 ms

        pdf_data = await page.pdf(**pdf_params)

        await browser.close()
        return pdf_data

    pool = concurrent.futures.ThreadPoolExecutor()
    # Create a temporary file to pass the HTML code to Chromium:
    # Unfortunately, tempfile on Windows does not allow for an already open
    # file to be opened by a separate process. So we must close it first
    # before calling Chromium. We also specify delete=False to ensure the
    # file is not deleted after closing (the default behavior).
    temp_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
    with temp_file:
        temp_file.write(html.encode("utf-8"))
    try:
        def run_coroutine(coro):
            """Run an internal coroutine."""
            loop = (
                asyncio.ProactorEventLoop()  # type:ignore[attr-defined]
                if IS_WINDOWS
                else asyncio.new_event_loop()
            )

            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)

        pdf_data = pool.submit(run_coroutine, main(temp_file)).result()
    finally:
        # Ensure the file is deleted even if playwright raises an exception
        os.unlink(temp_file.name)
    return pdf_data
################################################################################################


# execute main function:
if __name__ == "__main__":
    main()
    print()
