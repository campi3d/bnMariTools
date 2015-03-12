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
## Contributions: Jens Kafitz, 2015
## Contact: jens.kafitz@campi3d.com
############################################################



import mari
import PySide.QtGui as QtGui

USER_ROLE = 32          # PySide.Qt.UserRole

# ------------------------------------------------------------------------------


def _isProjectSuitable():
    """Checks project state and mari version"""
    MARI_2_6V3_VERSION_NUMBER = 20603300   # see below
    if mari.app.version().number() >= MARI_2_6V3_VERSION_NUMBER:
    
        if mari.projects.current() is None:
            mari.utils.message("Please open a project before running.")
            return False, False

        return True, False
        
    else:
        mari.utils.message("You can only run this script in Mari 2.6v3 or newer.")
        return False, False


# ------------------------------------------------------------------------------


def makeChannelLayer(sourceChannel, mode, invert):
    """Creates Channel Layer, channel Layer Mask or channel Layer mask grouped"""

    selectionData = getSelectedLayer().findSelection()
    currentStack = selectionData[2]
    currentLayer = selectionData[3]
    currentSelection = selectionData[4]

    layerName = currentLayer.name()
    
    

    if mode == 'layer':
        mari.history.startMacro('Create channel Layer')
        for channel in sourceChannel:
            channelLayerName = channel.name()
            currentStack.createChannelLayer(channelLayerName, channel, None, 16)
        mari.history.stopMacro()

    else:
        
        
        if mode == 'maskgroup':
            if currentLayer.isShaderLayer():
                mari.utils.message('Groups are not supported for Shader Layers')
                return
            else:
                try:
                    ## New Group Layer
                    layerName = currentLayer.name()
                    mari.history.startMacro('Create grouped channel mask')
                    layerGroupName = '%s_grp' % layerName
                    selectionData = getSelectedLayer().findSelection()
                    currentStack = selectionData[2]
                    groupLayer = currentStack.groupLayers([currentSelection], None, None, 16)
                    groupLayer.setName(layerGroupName)
                    layerMaskStack = groupLayer.makeMaskStack()
                    layerMaskStack.removeLayers(layerMaskStack.layerList()) 

                    ## Create Mask Channel Layer
                    
                    for channel in sourceChannel:
                        channelLayerName = channel.name()
                        maskChannelLayerName = '%s(Shared Channel)' % channelLayerName
                        layerMaskStack.createChannelLayer(maskChannelLayerName, channel)

                    if invert == 1:
                       layerMaskStack.createAdjustmentLayer("Invert","Filter/Invert")

                    mari.history.stopMacro()
        
                except Exception:
                    pass

        elif mode == 'mask':
            mari.history.startMacro('Create channel mask')

            for layer in currentSelection:          
                
                layerName = layer.name()
                currentLayer = layer
                
                ## New Layer Mask Stack.
                ## If mask exists convert, if stack exists keep, else make new stack
                if currentLayer.hasMaskStack():
                    layerMaskStack = currentLayer.maskStack()
                elif currentLayer.hasMask():
                    layerMaskStack = currentLayer.makeMaskStack()
                else:
                    layerMaskStack = currentLayer.makeMaskStack()
                    layerMaskStack.removeLayers(layerMaskStack.layerList())

                ## Create Mask Channel Layer
                
                for channel in sourceChannel:

                    channelLayerName = channel.name()
                    maskChannelLayerName = '%s(Shared Channel)' % channelLayerName
                    layerMaskStack.createChannelLayer(maskChannelLayerName, channel)  

                if invert == 1:
                    layerMaskStack.createAdjustmentLayer("Invert","Filter/Invert")

            mari.history.stopMacro()
    

# ------------------------------------------------------------------------------


class ChannelLayerUI(QtGui.QDialog):
    '''GUI to select channel to make into a channel-layer in the current channel
    modes: 'maskgroup', 'mask', 'layer'
    '''
    def __init__(self, mode):
        suitable = _isProjectSuitable()
        if suitable[0]:        
            super(ChannelLayerUI, self).__init__()
            self.setFixedSize(340, 400)
            #Set window title and create a main layout
            title = "Channel Layer"
            if mode is 'mask':
                title = "Channel Layer Mask"
            if mode is 'maskgroup':
                title = "Channel Layer Group Mask"
            self.setWindowTitle(title)
            main_layout = QtGui.QVBoxLayout()
            
            #Create layout for middle section
            centre_layout = QtGui.QHBoxLayout()
            
            #Create channel layout, label, and widget. Finally populate.
            channel_layout = QtGui.QVBoxLayout()
            channel_header_layout = QtGui.QHBoxLayout()
            channel_label = QtGui.QLabel("<strong>Channels</strong>")
            channel_list = QtGui.QListWidget()
            channel_list.setSelectionMode(channel_list.ExtendedSelection)
            
            #Create filter box for channel list
            channel_filter_box = QtGui.QLineEdit()
            mari.utils.connect(channel_filter_box.textEdited, lambda: self.updateChannelFilter(channel_filter_box, channel_list))
            
            #Create layout and icon/label for channel filter
            channel_header_layout.addWidget(channel_label)
            channel_header_layout.addStretch()
            channel_search_icon = QtGui.QLabel()
            search_pixmap = QtGui.QPixmap(mari.resources.path(mari.resources.ICONS) + '/Lookup.png')
            channel_search_icon.setPixmap(search_pixmap)
            channel_header_layout.addWidget(channel_search_icon)
            channel_header_layout.addWidget(channel_filter_box)
 
            #Populate Channel List, channellist gets full channel list from project and amount of channels on current object (which sit at the top of the list)
            channel_list= self.populateChannelList(channel_list)
   
            #Add filter layout and channel list to channel layout
            channel_layout.addLayout(channel_header_layout)
            channel_layout.addWidget(channel_list)

            
            #Add widgets to centre layout
            centre_layout.addLayout(channel_layout)
            
            #Create button layout and hook them up
            button_layout = QtGui.QHBoxLayout()
            ok_button = QtGui.QPushButton("&OK")
            cancel_button = QtGui.QPushButton("&Cancel")
            Invert_box = QtGui.QCheckBox('Invert Channel')
            if mode is not 'layer':
                button_layout.addWidget(Invert_box)
            button_layout.addStretch()
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
     

            #Hook up OK/Cancel button clicked signal to accept/reject slot
            ok_button.clicked.connect(lambda: self.runCreate(mode,channel_list,Invert_box.isChecked()))
            cancel_button.clicked.connect(self.reject)
            

            #Add layouts to main layout and dialog
            main_layout.addLayout(centre_layout)
            main_layout.addLayout(button_layout)
            self.setLayout(main_layout)


# ------------------------------------------------------------------------------

    def populateChannelList(self,channel_list):
		"Add channels to channel list"
		selectionData = getSelectedLayer().findSelection()
		geo = selectionData[0]
		cur_chan = selectionData[1]
		chan_list = sorted(geo.channelList(), key=lambda x: unicode.lower( x.name() ) )
		
		for channel in chan_list:
			shaderChannel = channel.isShaderStack()
			if channel is cur_chan:
				pass
			else:
				if not shaderChannel:
					channel_list.addItem(channel.name())
					channel_list.item(channel_list.count() - 1).setData(USER_ROLE, channel)
		
		return channel_list

# ------------------------------------------------------------------------------

    def updateChannelFilter(self,channel_filter_box, channel_list):
        "For each item in the channel list display, set it to hidden if it doesn't match the filter text."
        
        match_words = channel_filter_box.text().lower().split()
       
        for item_index in range(channel_list.count()):
            item = channel_list.item(item_index)
            item_text_lower = item.text().lower()
            matches = all([word in item_text_lower for word in match_words])
            item.setHidden(not matches)
    
    
# ------------------------------------------------------------------------------
   
    def selectedChannel(self,channel_list):
        "get channel selection"
        
        multiSelection = []
        for item in channel_list.selectedItems():
            multiSelection.append(item.data(USER_ROLE))

        return multiSelection


    
    def runCreate(self,mode,channel_list,invert):
        "execute channel layer creation"
        sourceChannel = self.selectedChannel(channel_list)
        makeChannelLayer(sourceChannel,mode,invert)
        self.close()


# ------------------------------------------------------------------------------    
# The following are used to find selections no matter where in the Mari Interface:
# returnTrue(),cl_getLayerList(),cl_findLayerSelection()
# 
# This is to support a) Layered Shader Stacks b) deeply nested stacks (maskstack,adjustment stacks),
# as well as cases where users are working in pinned or docked channels without it being the current channel
# ------------------------------------------------------------------------------

class getSelectedLayer():
    """Searches for Layer Selection in Substacks and searches for current channel if currentChannel is not the            
    selected one (when a channel is opened as floating or pinned palette)"""

    def __init__(self):
        curGeo = None
        curChannel = None
        curLayer = None
          

    def findSelection(self):
        """Searches for Layer Selection in Substacks and searches for current channel if currentChannel is not the            
        selected one (when a channel is opened as floating or pinned palette)"""

        curGeo = mari.current.geo()
        curChannel = mari.current.channel()
        curStack = curChannel
        curLayer = mari.current.layer()
        channels = curGeo.channelList()

        layerStacks = ()
        curSelList = []
        chn_layerList = ()
        layer = None
        stack = None   
        layerSelect = False
         
        if  curLayer.isSelected():
            chn_layerList = curChannel.layerList()
            layerStacks = self.cl_getLayerList(chn_layerList,curChannel,self.cl_returnTrue)

            for item in layerStacks:
                layer = item[1]
                stack = item[0]   
                if layer.isSelected():
                    curSelList.append(layer)
                    layerSelect = True
                    curStack = stack
                    curChannel = curChannel 

        else:
        
            for channel in channels:
                
                chn_layerList = channel.layerList()
                layerStacks = self.cl_getLayerList(chn_layerList,channel,self.cl_returnTrue)
            
                for item in layerStacks:
                    layer = item[1]
                    stack = item[0] 
                    if layer.isSelected():
                        curLayer = layer
                        curStack = stack
                        curChannel = channel
                        curSelList.append(layer)
                        layerSelect = True
        
        if not layerSelect:
            mari.utils.message('No Layer Selection found. \n \n Please select at least one Layer.')
 
        return curGeo,curChannel,curStack,curLayer,curSelList               



    def cl_returnTrue(self,layer):
        """Returns True for any object passed to it."""
        return True



    def cl_getLayerList(self,layer_list, stack, criterionFn):
        """Returns a list of all of the layers in the stack that match the given criterion function, including substacks."""
        matchingLayers = []
        tu = ()
        for layer in layer_list:
            if criterionFn(layer):
                tu = stack,layer
                matchingLayers.append(tu)
            if hasattr(layer, 'layerStack'):  
                matchingLayers.extend(self.cl_getLayerList(layer.layerStack().layerList(),layer.layerStack(),criterionFn))
            if layer.hasMaskStack():
                matchingLayers.extend(self.cl_getLayerList(layer.maskStack().layerList(),layer.maskStack(), criterionFn))
            if hasattr(layer, 'hasAdjustmentStack') and layer.hasAdjustmentStack():
                matchingLayers.extend(self.cl_getLayerList(layer.adjustmentStack().layerList(),layer.adjustmentStack(), criterionFn))


            
        return matchingLayers

# ------------------------------------------------------------------------------


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