from utemplate import source as ut_source

try:
    ut_source.Loader(None, "templates").load("page.html")
except ModuleNotFoundError:
    pass
