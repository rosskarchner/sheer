from shortstack.extensions.api import Extension


ext=Extension()

@ext.extendcontext_always
def sheer_template_functions():
    return {'queries':"foo"}
