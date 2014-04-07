"""Script to automatically generate OpenGLContext documentation"""
import pydoc2

if __name__ == "__main__":
	try:
		import wx
	except ImportError:
		pass
	else:
		class MyApp(wx.App):
			def OnInit(self):
				wx.InitAllImageHandlers()
				return True
		app = MyApp(0)
		app.MainLoop()

	excludes = [
		"math",
		"string",
	]
	stops = [
	]

	modules = [
		"basictypes",
		"basicproperty",
	]	
	pydoc2.PackageDocumentationGenerator(
		baseModules = modules,
		destinationDirectory = ".",
		exclusions = excludes,
		recursionStops = stops,
	).process ()
	