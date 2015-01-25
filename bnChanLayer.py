##  bnChanLayer Tool
############################################################
## Tool for creating channel layers.
## -------------------
## Install: Copy this file to your user Mari/Scripts folder.
## (Create a Scripts directory if there is none)
## Versions supported: 2.6+
## -------------------
## Copyright Ben Neall 2013-2014
## Contact: bneall@gmail.com
############################################################



from PySide import QtGui
import mari


def _isProjectSuitable():
    "Checks if Mari Version is compatible"
    MARI_2_6v3_VERSION_NUMBER =   20603300 #MARI 2.6v3

    if mari.app.version().number() >=  MARI_2_6v3_VERSION_NUMBER:

	return True, True

        if mari.app.version().number() >= 20603300:
            return True, True

        return True, False
        
    else:
        mari.utils.message("You can only run this script in Mari 2.6v3 or newer.")
        return False, False




def makeChannelLayer(sourceChannel, mode, invert):
	currentChannel = mari.geo.current().currentChannel()
	currentLayer = currentChannel.currentLayer()
	layerName = currentLayer.name()
	channelLayerName = sourceChannel.name()
	
	if mode == 'layer':
		mari.history.startMacro('Create channel Layer')
		currentChannel.createChannelLayer(channelLayerName, sourceChannel, None, 16)
		mari.history.stopMacro()
	else:
		
		
		if mode == 'maskgroup':
			## New Group Layer
			mari.history.startMacro('Create grouped channel mask')
			layerGroupName = '%s_grp' % layerName
			groupLayer = currentChannel.groupLayers([currentLayer], None, None, 16)
			groupLayer.setName(layerGroupName)
			layerStack = groupLayer
		elif mode == 'mask':
			mari.history.startMacro('Create channel mask')
			layerStack = currentLayer



		
		## New Layer Mask Stack
		layerMaskStack = layerStack.makeMaskStack()
		layerMaskStack.removeLayers(layerMaskStack.layerList())
		
		## Create Mask Channel Layer
		maskChannelLayerName = '%s(Shared Channel)' % channelLayerName
		layerMaskStack.createChannelLayer(maskChannelLayerName, sourceChannel)

		if invert == 1:
			layerMaskStack.createAdjustmentLayer("Invert","Filter/Invert")
	
		mari.history.stopMacro()

class ChannelLayerUI(QtGui.QDialog):
	'''GUI to select channel to make into a channel-layer in the current channel
	modes: 'groupmask', 'mask', 'layer'
	'''
	def __init__(self, mode):
		suitable = _isProjectSuitable()
		if suitable[0]:
			super(ChannelLayerUI, self).__init__()
			## Dialog Settings
			self.setFixedSize(300, 100)
			self.setWindowTitle('Select Channel')
			## Vars
			self.mode = mode
			## Layouts
			layoutV1 = QtGui.QVBoxLayout()
			layoutH1 = QtGui.QHBoxLayout()
			self.setLayout(layoutV1)
			## Widgets
			self.chanCombo = QtGui.QComboBox()
			self.okBtn = QtGui.QPushButton('Ok')
			self.cancelBtn = QtGui.QPushButton('Cancel')
			self.invertBtn = QtGui.QCheckBox('Invert')
			## Populate 
			layoutV1.addWidget(self.chanCombo)
			layoutV1.addLayout(layoutH1)
			layoutH1.addWidget(self.cancelBtn)
			layoutH1.addWidget(self.okBtn)
			if mode is not 'layer':
				layoutH1.addWidget(self.invertBtn)
			## Connections
			self.okBtn.clicked.connect(self.runCreate)
			self.cancelBtn.clicked.connect(self.close)
			## Init
			self.init()
	
	def init(self):
		currentChannel = mari.geo.current().currentChannel()
		channelList = mari.geo.current().channelList()
		for channel in channelList:
			if channel is not currentChannel:
				self.chanCombo.addItem(channel.name(), channel)
	
	def selectedChannel(self):
		return self.chanCombo.itemData(self.chanCombo.currentIndex(),32)

	def invertChannel(self):
		return self.invertBtn.isChecked()

	
	def runCreate(self):
		sourceChannel = self.selectedChannel()
		invert = self.invertChannel()
		makeChannelLayer(sourceChannel, self.mode,invert)
		self.close()


######################################################################
# Channel Layer UI Integration
######################################################################

###  Channel Layer ###

UI_path = 'MainWindow/&Layers'
script_menu_path = 'MainWindow/Scripts/Layers'

chanLayer = mari.actions.create('Add Channel Layer', 'ChannelLayerUI("layer").exec_()')
mari.menus.addAction(chanLayer, UI_path, 'Add Adjustment Layer')
mari.menus.addAction(chanLayer, script_menu_path)

icon_filename = 'linked.png'
icon_path = mari.resources.path(mari.resources.ICONS) + '/' + icon_filename
chanLayer.setIconPath(icon_path)
chanLayer.setShortcut('')

chanLayer.setEnabled(False)

### Channel Mask ###

UI_path = 'MainWindow/&Layers/Layer Mask/Add Mask'
script_menu_path = 'MainWindow/Scripts/Layers/Layer Mask'

chanMask = mari.actions.create('Add Channel Mask', 'ChannelLayerUI("mask").exec_()')
mari.menus.addAction(chanMask, UI_path)
mari.menus.addAction(chanMask, script_menu_path)

icon_filename = 'linked.png'
icon_path = mari.resources.path(mari.resources.ICONS) + '/' + icon_filename
chanMask.setIconPath(icon_path)
chanMask.setShortcut('')

chanMask.setEnabled(False)

### Channel Mask Group ###

UI_path = 'MainWindow/&Layers/Layer Mask/Add Mask'
script_menu_path = 'MainWindow/Scripts/Layers/Layer Mask'

chanMaskGrp = mari.actions.create('Add grouped Channel Mask', 'ChannelLayerUI("maskgroup").exec_()')
mari.menus.addAction(chanMaskGrp, UI_path)
mari.menus.addAction(chanMaskGrp, script_menu_path)

icon_filename = 'NewFolder.png'
icon_path = mari.resources.path(mari.resources.ICONS) + '/' + icon_filename
chanMaskGrp.setIconPath(icon_path)
chanMaskGrp.setShortcut('')

chanMaskGrp.setEnabled(False)


## Mari UI Init ##
def toggleUI():
	if mari.projects.current():
		chanLayer.setEnabled(True)
		chanMask.setEnabled(True)
		chanMaskGrp.setEnabled(True)
	elif not mari.projects.current():
		chanLayer.setEnabled(False)
		chanMask.setEnabled(False)
		chanMaskGrp.setEnabled(False)


## Connections
mari.utils.connect(mari.projects.openedProject, toggleUI)
mari.utils.connect(mari.projects.projectClosed, toggleUI)