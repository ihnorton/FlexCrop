import os
import unittest
from __main__ import vtk, qt, ctk, slicer

#
# FlexCrop
#

class FlexCrop:
  def __init__(self, parent):
    parent.title = "FlexCrop" # TODO make this more human readable by adding spaces
    parent.categories = ["Utilities"]
    parent.dependencies = []
    parent.contributors = ["Isaiah Norton (Brigham & Women's Hospital)"]
    parent.helpText = """
    Crop tool without axis restrictions.
    """
    parent.acknowledgementText = """
"""
    self.parent = parent

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['FlexCrop'] = self.runTest

  def runTest(self):
    tester = FlexCropTest()
    tester.runTest()

#
# qFlexCropWidget
#

class FlexCropWidget:
  def __init__(self, parent = None):
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()
    self.oldTarget = None

################################################################################
# Reloading harness
################################################################################
  def make_reloader(self):
    # Reload and Test area
    #
    reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    reloadCollapsibleButton.text = "Reload && Test"
    self.layout.addWidget(reloadCollapsibleButton)
    reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)

    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "FlexCrop Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)

    # reload and test button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadAndTestButton = qt.QPushButton("Reload and Test")
    self.reloadAndTestButton.toolTip = "Reload this module and then run the self tests."
    reloadFormLayout.addWidget(self.reloadAndTestButton)
    self.reloadAndTestButton.connect('clicked()', self.onReloadAndTest)

  def set_selector_options(self, node):
    node.selectNodeUponCreation = True
    node.addEnabled = False
    node.removeEnabled = False
    node.noneEnabled = False
    node.showHidden = False
    node.showChildNodeTypes = False
    
  def onReloadAndTest(self):
    pass
    
  def setup(self):
    # Instantiate and connect widgets ...
    self.make_reloader()
    self.createMaskFrame()
    self.createRegFrame()
    
    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    pass
  
  def onReload(self,moduleName="FlexCrop"):
    """Generic reload method for any scripted module.
    ModuleWizard will subsitute correct default moduleName.
    """
    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)
    
  def onClearMaskedButton(self):
    nodes = slicer.util.getNodes("vtkMRMLScalarVolumeNode*")
    for n in nodes:
        if "masked" in n:
            slicer.mrmlScene.RemoveNode(nodes[n])

  def onClearUnmaskedButton(self):
    nodes = slicer.util.getNodes("vtkMRMLScalarVolumeNode*")
    for n in nodes:
        if not "masked" in n:
            slicer.mrmlScene.RemoveNode(nodes[n])
            
  def onSelect(self):
    self.applyButton.enabled = self.nodeSelector.currentNode()

  def onApplyButton(self):
    logic = FlexCropLogic()
    inPlace = self.inPlaceCheckBox.checked
    logic.run(self.roiSelector.currentNode(), self.nodeSelector.checkedNodes(), inPlace)

  def onTargetSelected(self, node):
    # apparently this has no effect
    # http://www.na-mic.org/Bug/view.php?id=3589
    # self.regVolumesSelector.setUserCheckable(node, True)
    self.registerButton.enabled = True
    
  def onRegisterButton(self):
    logic = FlexCropLogic()
    logic.runRegistration(self.regTargetSelector.currentNode(), self.regVolumesSelector.checkedNodes())

  def createRegFrame(self):   
    #
    # Parameters Area
    #
    regCollapsibleButton = ctk.ctkCollapsibleButton()
    regCollapsibleButton.text = "Parameters"
    self.layout.addWidget(regCollapsibleButton)

    # Layout within the dummy collapsible button
    regFormLayout = qt.QFormLayout(regCollapsibleButton)
    
    #
    # target volume selector
    #
    self.regTargetSelector = slicer.qMRMLNodeComboBox()
    self.regTargetSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.regTargetSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.set_selector_options(self.regTargetSelector)
    self.regTargetSelector.setToolTip( "Pick the input to the algorithm." )
    regFormLayout.addRow("Target Volume: ", self.regTargetSelector)

    #
    # moving volume selector
    #
    self.regVolumesSelector = slicer.qMRMLCheckableNodeComboBox()
    self.regVolumesSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.regVolumesSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.set_selector_options(self.regVolumesSelector)
    self.regVolumesSelector.setToolTip( "Pick the input to the algorithm." )
    regFormLayout.addRow("Moving Volumes: ", self.regVolumesSelector)
    
    #
    # Apply Button
    #
    self.registerButton = qt.QPushButton("Register")
    self.registerButton.toolTip = "Register Images"
    self.registerButton.enabled = False
    regFormLayout.addRow(self.registerButton)

    # Connections before scene
    self.registerButton.connect('clicked(bool)', self.onRegisterButton)
    self.regTargetSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onTargetSelected)
    
    # Set MRML scenes
    self.regVolumesSelector.setMRMLScene( slicer.mrmlScene )
    self.regTargetSelector.setMRMLScene( slicer.mrmlScene )
    
  def createMaskFrame(self):
    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)
        
    #
    # input volume selector
    #
    self.nodeSelector = slicer.qMRMLCheckableNodeComboBox()
    self.nodeSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.nodeSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.set_selector_options(self.nodeSelector)
    self.nodeSelector.setMRMLScene( slicer.mrmlScene )
    self.nodeSelector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Input Volumes: ", self.nodeSelector)

    #
    # annotation ROI selector
    #
    self.roiSelector = slicer.qMRMLNodeComboBox()
    self.roiSelector.nodeTypes = ( ("vtkMRMLAnnotationROINode"), "" )
    #self.roiSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.set_selector_options(self.roiSelector)
    self.roiSelector.setMRMLScene( slicer.mrmlScene )
    self.roiSelector.setToolTip( "Pick the ROI for the masking." )
    parametersFormLayout.addRow("Mask ROI: ", self.roiSelector)

    #
    # check box to trigger taking screen shots for later use in tutorials
    #
    self.inPlaceCheckBox = qt.QCheckBox()
    self.inPlaceCheckBox.checked = 0
    self.inPlaceCheckBox.setToolTip("If checked, will operate in-place.")
    # TODO: make option to duplicate nodes
    parametersFormLayout.addRow("Mask in-place", self.inPlaceCheckBox)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.nodeSelector.connect("checkedNodesChanged()", self.onSelect)

    #
    # Helper Area
    #
    helperCollapsibleButton = ctk.ctkCollapsibleButton()
    helperCollapsibleButton.text = "Utilities"
    self.layout.addWidget(helperCollapsibleButton)

    # Layout within the dummy collapsible button
    helperFormLayout = qt.QFormLayout(helperCollapsibleButton)
    
    #
    # Clear Unmasked Images Button
    #
    self.clearImagesButton = qt.QPushButton("Clear Unmasked Images")
    self.clearImagesButton.toolTip = "Remove unmasked from scene."
    helperFormLayout.addRow(self.clearImagesButton)
    self.clearImagesButton.connect('clicked(bool)', self.onClearUnmaskedButton)
    
    #
    # Clear Masked Images Button
    #
    self.clearImagesButton = qt.QPushButton("Clear Masked Images")
    self.clearImagesButton.toolTip = "Remove masked from scene."
    helperFormLayout.addRow(self.clearImagesButton)
    self.clearImagesButton.connect('clicked(bool)', self.onClearMaskedButton)
    
################################################################################
# Logic
################################################################################

class FlexCropLogic:
  """This class should implement all the actual 
  computation done by your module.  The interface 
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """
  def __init__(self):
    pass

  def hasImageData(self,volumeNode):
    """This is a dummy logic method that 
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      print('no volume node')
      return False
    if volumeNode.GetImageData() == None:
      print('no image data')
      return False
    return True

  def delayDisplay(self,message,msec=1000):
    #
    # logic version of delay display
    #
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def runMasking(self,roiNode,inputVolumes,inPlace):
    """
    Run the actual algorithm
    """

    self.delayDisplay('Running the algorithm')

    for vol in inputVolumes:
        self.maskVolume(vol, roiNode, inPlace)

    return True

    self.delayDisplay('Running the aglorithm')

  def runRegistration(self,targetVol,movingVolumes):
    """
    Run the registration
    """

    self.delayDisplay('Running the algorithm')

    for movingVol in movingVolumes:
        self.registerVolumes(targetVol, movingVol)

    return True

    self.delayDisplay('Running registration')    

  def registerVolumes(self, targetVol, movingVol):
 
    # Set up transformations
    tfmName = movingVol.GetName() + " ---TO--- " + targetVol.GetName()
    tfmNode = movingVol.GetParentTransformNode()
    if tfmNode == None or (tfmNode != None and tfmNode.GetName() != tfmName):
      nodeFactory = slicer.qMRMLNodeFactory()
      nodeFactory.setMRMLScene(slicer.mrmlScene)
      tfmNode = nodeFactory.createNode('vtkMRMLLinearTransformNode')
      tfmNode.SetName(tfmName)
      movingVol.SetAndObserveTransformNodeID(tfmNode.GetID())
    
    # Brainsfit parameters
    parameters = {}
    parameters['fixedVolume'] = targetVol
    parameters['movingVolume'] = movingVol
    parameters['outputTransform'] = tfmNode.GetID()
    parameters['initializeTransformMode'] = 'useMomentsAlign'
    parameters['useRigid'] = True
    
    brainsFit = slicer.modules.brainsfit
    cliNode = slicer.cli.run(brainsFit, None, parameters, wait_for_completion = True)

  def maskVolume(self, volumeIn, roiNode, inPlace=False):
    # Clone input volume, unless inPlace
    inPlace = False # TODO: make this work
    
    nameout = volumeIn.GetName()
    if not "masked" in nameout:
        nameout += " masked"
    
    if inPlace:
        outData = vtk.vtkImageData()
        volumeIn.SetName(volumeIn.GetName() + " masked")
    else:
        volumeOut = slicer.modules.volumes.logic().CloneVolume(volumeIn, nameout)
        outData = volumeOut.GetImageData()

    # Get transform into image space
    IJKtoRAS = vtk.vtkMatrix4x4()
    volumeIn.GetIJKToRASMatrix(IJKtoRAS)

    # Get ROI to image transform
    ROItoImage = vtk.vtkMatrix4x4()
    ROItoImage.Identity()
    parentNode = roiNode.GetParentTransformNode()
    if parentNode is None and volumeIn.GetParentTransformNode():
      volumeIn.GetParentTransformNode().GetMatrixTransformToWorld(ROItoImage)
      # don't invert here, this is already the proper direction.
    if parentNode is not None:
      parentNode.GetMatrixTransformToNode(volumeIn.GetParentTransformNode(), ROItoImage)
      ROItoImage.Invert()
    
    # Transformations
    tfm = vtk.vtkTransform()
    tfm.SetMatrix(IJKtoRAS)
    tfm.PostMultiply()
    tfm.Concatenate(ROItoImage)

    # Get planes and apply transform
    planes = vtk.vtkPlanes()
    roiNode.GetTransformedPlanes(planes)
    planes.SetTransform(tfm)

    # Blot out selected region
    tostencil = vtk.vtkImplicitFunctionToImageStencil()
    tostencil.SetInput(planes)
    imgstencil = vtk.vtkImageStencil()
    imgstencil.SetInput(volumeIn.GetImageData())
    imgstencil.SetStencil(tostencil.GetOutput())
    imgstencil.SetBackgroundValue(0)
    imgstencil.ReverseStencilOn()

    # Write the changes
    imgstencil.SetOutput(outData)
    imgstencil.Update()
    
################################################################################
# Testing
################################################################################

class FlexCropTest(unittest.TestCase):
  """
  This is the test case for your scripted module.
  """

  def delayDisplay(self,message,msec=1000):
    """This utility method displays a small dialog and waits.
    This does two things: 1) it lets the event loop catch up
    to the state of the test so that rendering and widget updates
    have all taken place before the test continues and 2) it
    shows the user/developer/tester the state of the test
    so that we'll know when it breaks.
    """
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_FlexCrop1()

  def test_FlexCrop1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests sould exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """
