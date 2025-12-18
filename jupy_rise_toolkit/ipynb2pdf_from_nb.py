import sys, os, string
import ipynbname, nbformat
import numpy as np
from glob import glob
from natsort import natsorted
from pypdf import PdfWriter

# copy notebook first to avoid infinite loops
# delete any instances of the two functions above
def copy_notebook():
    
    nb_name = ipynbname.name()
    with open(nb_name + '.ipynb', 'r') as f:
        
        # read current nb
        nb = nbformat.read(f, as_version=4)

        # remove all instances of copy_notebook() for copy
        nb['cells'] = [ cell for cell in nb['cells'] if ( cell['cell_type'] != 'code' or not ('copy_notebook()' in cell['source'] or
                                                                                              'ipynb2pdf(' in cell['source'] ) ) ]
        
        # generate new name
        characters = [char for char in string.ascii_letters + string.digits]
        size = 16
        random_appendix = ''.join(np.random.choice(characters, size=size, replace=True))  
        nb_copy_name = nb_name + random_appendix + '.ipynb'
        
        with open(nb_copy_name, 'w') as f:
            nbformat.write(nb, f)
        
        return nb_name, random_appendix


# file name of merged pdf
# output_filename = 'script.pdf'

# custom bookmarks (if None file names are used)
# should be a list (of strings) of length >= to the number of merged pdfs
# custom_bookmarks = []

# optional list of notebooks that should be excluded from the conversion
# ipynb_filter = ['06_V_StetigeVerteilungen_PDFVersion.ipynb']
# ipynb_filter = []

# default arguments/parameters for conversion
# arg_default = ['-hide-tag', '-ex', '-no-overwrite']



def ipynb2pdf( 
        output_filename: str = 'script.pdf',
        custom_bookmarks: list[str] = [],
        ipynb_filter: list[str] = [],
        hide_tag: str =  ' --TagRemovePreprocessor.enabled=True --TagRemovePreprocessor.remove_input_tags hide',
        execute: str = ' --execute',
        overwrite: str = ' --no-overwrite',
        show_input: str = ' --no-input',
        delete_temp: Bool = True
        ):
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
    
    only merge pdf files (needs pdf files):
        python ipynb2pdf.py -merge
    
    create pdf files and merge:
        python ipynb2pdf.py -pdf -merge
        
    additional parameters:
        -no-input       hide input cells with python code (displayed by default)
        -hide-tag       remove all input cells with cell tag "hide" (overwrites -no-input)
        -ex             re-execute notebooks (off by default; necessary for correct display of widgets)
        -no-overwrite   only convert notebooks that are not already converted
                        (by default all notebooks are converted overwriting already existing files)
        -slides         use html slides as output format # TODO: Latex definitions are not working across different slides!
    """

    # get notebook name and copy notebook
    nb_name, appendix_of_current_nb = copy_notebook()

    # get all ipynb files in current directory
    list_ipynb = glob('*.ipynb')
        
    # remove executing notebook to avoid infinite loop
    list_ipynb.remove(nb_name + '.ipynb')
    
    # filter ipynb files
    list_ipynb = [n for n in list_ipynb if n not in ipynb_filter]

    # get all cenverted files (*.html.pdf)
    list_converted = [p.split('.html.pdf')[0] for p in glob('*.html.pdf')]
    
    # net yet converted ipynb files
    list_ipynb_new = [nb for nb in list_ipynb if nb.split('.ipynb')[0] not in list_converted]
    
    list_ipynb = list_ipynb_new if ( overwrite == '-no-overwrite' ) else list_ipynb
    list_names = [n.split('.ipynb')[0] for n in list_ipynb]
    # list_names = [s.split(appendix_of_current_nb)[0] for s in list_names]

    # handle additional parameters:
    # execute = ' --execute' if (execute == '-ex') else ''
    # show_input = ' --no-input' if (show_input == '-no-input') else ''
    # output_type = 'slides' if ('-slides' in arg) else 'html'
    # hide_tag = ' --TagRemovePreprocessor.enabled=True --TagRemovePreprocessor.remove_input_tags hide' if ('-hide-tag' in arg) else ''
    if hide_tag:
        show_input = ''

    # if no steps are specified all steps should be executed
    do_all_steps = True # ('-html' not in arg) and ('-pdf' not in arg) and ('-merge' not in arg)
    
    print(list_ipynb)
    print(list_names)
    
    # 1. convert all jupyter notebooks to html with nbconvert:
    if do_all_steps: # or ('-html' in arg)
        if list_ipynb: # if not empty!
            # print(f'python -m nbconvert --to html ' + ' '.join(list_ipynb) + show_input + execute + hide_tag)
            os.system(f'python -m nbconvert --to html ' + ' '.join(list_ipynb) + show_input + execute + hide_tag)


    # 2. convert html files to pdf with playwright (using chromium):
    
    # pdf formatting options
    pdf_params = {
        # see: https://playwright.dev/docs/api/class-page#page-pdf
        "format": 'A4',
        "scale": 0.7,
        "landscape": False,
        "print_background": True,
        "margin": {
            "top": "0.0cm",
            "right": "0.0cm",
            "bottom": "0.0cm",
            "left": "0.0cm",
            },
    }

    # to correctly display latex formulas we have to wait for mathjax to finish
    # TODO: wait for a specific event and not for a fixed amount of time?
    wait_for_mathjax_timeout = 10000 # ms

    if do_all_steps: # or ('-pdf' in arg)
        file_ext = '.html' # '.slides.html' if output_type == 'slides' else 
        html_files = [n + file_ext for n in list_names]
        
        for html_file in html_files:
            print('converting to pdf:', html_file)
                
            with open(html_file, "r", encoding='utf-8') as f:
                html = f.read()

            pdf_data = run_playwright(html, pdf_params=pdf_params, timeout=wait_for_mathjax_timeout)

            with open(html_file + '.pdf', "wb") as f:
                f.write(pdf_data)

            if delete_temp:
                os.remove(html_file)


    # 3. merge pdfs and create bookmarks:
    if do_all_steps: # ('-merge' in arg) or 
        if not list_ipynb:
            return # skip merge if no (new) files 
        file_ext = 'html.pdf' # 'slides.html.pdf' if output_type == 'slides' else
        pdf_files = natsorted(glob('*.' + file_ext)) # here the order is important!

        file_names = [f.split('.html.pdf')[0] for f in pdf_files]
        bookmarks = custom_bookmarks if custom_bookmarks else file_names

        merger = PdfWriter()
        for pdf_file, bookmark in zip(pdf_files, bookmarks):
            if pdf_file == output_filename:
                continue
            print("appending:", pdf_file)
            merger.append(pdf_file, bookmark)

            if delete_temp:
                os.remove(pdf_file)

        merger.write(output_filename)
        merger.close()


################################################################################################
# 'run_playwright' function copied (and modified) from nbconvert webpdf exporter:

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
        await playwright.stop()
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
        pdf_data = pool.submit(asyncio.run, main(temp_file)).result()
    finally:
        # Ensure the file is deleted even if playwright raises an exception
        os.unlink(temp_file.name)
    return pdf_data

################################################################################################