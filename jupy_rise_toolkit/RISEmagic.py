def hide():   
    from IPython import display
    import binascii
    import os
    uid = binascii.hexlify(os.urandom(8)).decode()    
    html = """<div id="%s"></div>
    <script type="text/javascript">
        $(function(){
            var p = $("#%s");
            if (p.length==0) return;
            while (!p.hasClass("cell")) {
                p=p.parent();
                if (p.prop("tagName") =="body") return;
            }
            var cell = p;
            cell.find(".input").addClass("notvisible")
        });
    </script>""" % (uid, uid)
    display.display_html(html, raw=True)

from html.parser import HTMLParser
class NBParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        self.attr = {attr[0] : attr[1] for attr in attrs}

p = NBParser()
p.feed('<rise slide="fragment"/>')
p.attr['slide']
