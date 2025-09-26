import os
import nbformat

def create_template(
        author: str = 'Author',
        title: str = 'Titel',
        date: str = '', 
        path: str = '',
        filename: str = 'my_notebook' ):
    
    # create new notebook
    nb = nbformat.v4.new_notebook() 

    # add tilte 
    cell_title = nbformat.v4.new_markdown_cell( '# ' + title )
    nb['cells'].append( cell_title )

    # add packages
    cell_packages = nbformat.v4.new_code_cell( 'import numpy as np' )
    nb['cells'].append( cell_packages )

    # add metadata TODO

    nb['metadata'].update({
        "rise": {
            "enable_chalkboard": True,
            "footer": "<div style=\"padding-left:6em;padding-bottom:0.1em;font-size:3em;\">" + 
                        author + ": &nbsp; <i>" + title + "</i><img src=\"TU_Logo_SVG_crop.svg\" alt=\"TU Ilmenau\" height=\"120%\" style=\"padding-left:9em;;padding-bottom:0.3em\"></div>",
            "history": False,
            "progress": True,
            "reveal_shortcuts": {
                "chalkboard": {
                    "download": "d",
                    "toggleChalkboard": "shift-b",
                    "toggleNotesCanvas": "shift-a"
                }
            },
            "scroll": True
        }
    })

    # write to file
    cd = os.getcwd()

    with open( filename + '.ipynb', 'w' ) as f:
	    nbformat.write(nb, f)

if __name__ == "__main__":
      create_template( filename = 'Workshop' )