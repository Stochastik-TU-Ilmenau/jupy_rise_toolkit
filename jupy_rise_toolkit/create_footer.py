# import nbformat
# import sys
# import re
# import IPython

# <div style="padding-left:6em;padding-bottom:0.1em;font-size:3em;">
# Thomas Hotz: &nbsp; <i>Stochastik für Mathematiker</i>
# <img src="TU_Logo_SVG_crop.svg" alt="TU Ilmenau" 
# height="120%" style="padding-left:9em;;padding-bottom:0.3em"></div>

def create_footer( author, course, logo = "TU_Logo_SVG_crop.svg" ):

    footer = ''
    footer += '<div style="padding-left:6em;padding-bottom:0.1em;font-size:3em;">'
    footer += author + ': &nbsp; <i>'
    footer += course + '</i><img src="'
    footer += logo + '" alt="TU Ilmenau" height="120%" style="padding-left:9em;;padding-bottom:0.3em"></div>'

    return footer

if __name__ == "__main__":
    footer = create_footer( 'Maxi Mustermensch', 'Stochastik')
    print(footer)