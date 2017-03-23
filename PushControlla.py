from __future__ import with_statement

import Live
from _Framework.ControlSurface import ControlSurface
from _Framework.InputControlElement import *
from _Framework.SliderElement import SliderElement
from _Framework.ButtonElement import ButtonElement
from _Framework.ButtonMatrixElement import ButtonMatrixElement
from _Framework.ChannelStripComponent import ChannelStripComponent
from _Framework.DeviceComponent import DeviceComponent
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from _Framework.SessionZoomingComponent import SessionZoomingComponent
from SpecialMixerComponent import SpecialMixerComponent
from SpecialTransportComponent import SpecialTransportComponent
from SpecialSessionComponent import SpecialSessionComponent
from SpecialZoomingComponent import SpecialZoomingComponent
from SpecialViewControllerComponent import DetailViewControllerComponent
from MIDI_Map import *
#MIDI_NOTE_TYPE = 0
#MIDI_CC_TYPE = 1
#MIDI_PB_TYPE = 2

class PushControlla(ControlSurface):
    __doc__ = " Script for PushControlla in APC emulation mode "

    _active_instances = []
    def _combine_active_instances():
        track_offset = 0
        scene_offset = 0
        for instance in PushControlla._active_instances:
            instance._activate_combination_mode(track_offset, scene_offset)
            track_offset += instance._session.width()
    _combine_active_instances = staticmethod(_combine_active_instances)

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        #self.set_suppress_rebuild_requests(True)
        with self.component_guard():
            self._note_map = []
            self._ctrl_map = []
            self._load_MIDI_map()
            self._session = None
            self._session_zoom = None
            self._mixer = None
            self._setup_session_control()
            self._setup_mixer_control()
            self._session.set_mixer(self._mixer)
            self._setup_device_and_transport_control()
            self.set_highlighting_session_component(self._session)
            #self.set_suppress_rebuild_requests(False)
        self._pads = []
        self._load_pad_translations()
        self._do_combine()


    def disconnect(self):
        self._note_map = None
        self._ctrl_map = None
        self._pads = None
        self._do_uncombine()
        self._shift_button = None
        self._session = None
        self._session_zoom = None
        self._mixer = None
        ControlSurface.disconnect(self)


    def _do_combine(self):
        if self not in PushControlla._active_instances:
            PushControlla._active_instances.append(self)
            PushControlla._combine_active_instances()


    def _do_uncombine(self):
        if ((self in PushControlla._active_instances) and PushControlla._active_instances.remove(self)):
            self._session.unlink()
            PushControlla._combine_active_instances()


    def _activate_combination_mode(self, track_offset, scene_offset):
        if TRACK_OFFSET != -1:
            track_offset = TRACK_OFFSET
        if SCENE_OFFSET != -1:
            scene_offset = SCENE_OFFSET
        self._session.link_with_track_offset(track_offset, scene_offset)


    def _setup_session_control(self):
        is_momentary = True
        self._session = SpecialSessionComponent(8, 4)
        self._session.name = 'Session_Control'
        self._session.set_track_bank_buttons(self._ctrl_map[SESSIONRIGHT], self._ctrl_map[SESSIONLEFT])
        self._session.set_scene_bank_buttons(self._ctrl_map[SESSIONDOWN], self._ctrl_map[SESSIONUP])
        self._session.set_select_buttons(self._ctrl_map[SCENEDN], self._ctrl_map[SCENEUP])
        self._scene_launch_buttons = [self._ctrl_map[SCENELAUNCH[index]] for index in range(4)]
        self._track_stop_buttons = [self._note_map[TRACKSTOP[index]] for index in range(8)]
        self._session.set_stop_all_clips_button(self._ctrl_map[STOPALLCLIPS])
        self._session.set_stop_track_clip_buttons(tuple(self._track_stop_buttons))
        self._session.selected_scene().name = 'Selected_Scene'
        self._session.selected_scene().set_launch_button(self._ctrl_map[SELSCENELAUNCH])
        self._session.set_slot_launch_button(self._note_map[SELCLIPLAUNCH])
        for scene_index in range(4):
            scene = self._session.scene(scene_index)
            scene.name = 'Scene_' + str(scene_index)
            button_row = []
            scene.set_launch_button(self._scene_launch_buttons[scene_index])
            scene.set_triggered_value(2)
            for track_index in range(8):
                button = self._note_map[CLIPNOTEMAP[scene_index][track_index]]
                button_row.append(button)
                clip_slot = scene.clip_slot(track_index)
                clip_slot.name = str(track_index) + '_Clip_Slot_' + str(scene_index)
                clip_slot.set_launch_button(button)
        self._session_zoom = SpecialZoomingComponent(self._session)
        self._session_zoom.name = 'Session_Overview'
        self._session_zoom.set_nav_buttons(self._note_map[ZOOMUP], self._note_map[ZOOMDOWN], self._note_map[ZOOMLEFT], self._note_map[ZOOMRIGHT])

    def _setup_mixer_control(self):
        is_momentary = True
        self._mixer = SpecialMixerComponent(8)
        self._mixer.name = 'Mixer'
        self._mixer.master_strip().name = 'Master_Channel_Strip'
        self._mixer.master_strip().set_select_button(self._ctrl_map[MASTERSEL])
        self._mixer.selected_strip().name = 'Selected_Channel_Strip'
        self._mixer.set_select_buttons(self._ctrl_map[TRACKRIGHT], self._ctrl_map[TRACKLEFT])
        self._mixer.set_crossfader_control(self._ctrl_map[CROSSFADER])
        self._mixer.set_prehear_volume_control(self._ctrl_map[CUELEVEL])
        self._mixer.master_strip().set_volume_control(self._ctrl_map[MASTERVOLUME])
        for track in range(8):
            strip = self._mixer.channel_strip(track)
            strip.name = 'Channel_Strip_' + str(track)
            strip.set_arm_button(self._ctrl_map[TRACKREC[track]])
            strip.set_solo_button(self._ctrl_map[TRACKSOLO[track]])
            strip.set_mute_button(self._ctrl_map[TRACKMUTE[track]])
            strip.set_select_button(self._ctrl_map[TRACKSEL[track]])
            strip.set_volume_control(self._ctrl_map[TRACKVOL[track]])
            strip.set_pan_control(self._ctrl_map[TRACKPAN[track]])
            strip.set_send_controls((self._ctrl_map[TRACKSENDA[track]], self._ctrl_map[TRACKSENDB[track]], self._ctrl_map[TRACKSENDC[track]]))
            strip.set_invert_mute_feedback(True)


    def _setup_device_and_transport_control(self):
        is_momentary = True
        self._device = DeviceComponent()
        self._device.name = 'Device_Component'
        device_bank_buttons = []
        device_param_controls = []
        for index in range(8):
            device_param_controls.append(self._ctrl_map[PARAMCONTROL[index]])
            device_bank_buttons.append(self._note_map[DEVICEBANK[index]])
        if None not in device_bank_buttons:
            self._device.set_bank_buttons(tuple(device_bank_buttons))
        if None not in device_param_controls:
            self._device.set_parameter_controls(tuple(device_param_controls))
        self._device.set_on_off_button(self._note_map[DEVICEONOFF])
        self._device.set_bank_nav_buttons(self._note_map[DEVICEBANKNAVLEFT], self._note_map[DEVICEBANKNAVRIGHT])
        self._device.set_lock_button(self._note_map[DEVICELOCK])
        self.set_device_component(self._device)

        detail_view_toggler = DetailViewControllerComponent()
        detail_view_toggler.name = 'Detail_View_Control'
        detail_view_toggler.set_device_clip_toggle_button(self._note_map[CLIPTRACKVIEW])
        detail_view_toggler.set_detail_toggle_button(self._note_map[DETAILVIEW])
        detail_view_toggler.set_device_nav_buttons(self._note_map[DEVICENAVLEFT], self._note_map[DEVICENAVRIGHT] )

        transport = SpecialTransportComponent()
        transport.name = 'Transport'
        transport.set_play_button(self._ctrl_map[PLAY])
        transport.set_stop_button(self._ctrl_map[STOP])
        transport.set_record_button(self._ctrl_map[REC])
        transport.set_nudge_buttons(self._note_map[NUDGEUP], self._note_map[NUDGEDOWN])
        transport.set_undo_button(self._note_map[UNDO])
        transport.set_redo_button(self._note_map[REDO])
        transport.set_tap_tempo_button(self._ctrl_map[TAPTEMPO])
        transport.set_quant_toggle_button(self._ctrl_map[RECQUANT])
        transport.set_overdub_button(self._note_map[OVERDUB])
        transport.set_metronome_button(self._ctrl_map[METRONOME])
        transport.set_tempo_control(self._ctrl_map[TEMPOCONTROL])
        transport.set_loop_button(self._note_map[LOOP])
        transport.set_seek_buttons(self._note_map[SEEKFWD], self._note_map[SEEKRWD])
        transport.set_punch_buttons(self._note_map[PUNCHIN], self._note_map[PUNCHOUT])
        ##transport.set_song_position_control(self._ctrl_map[SONGPOSITION]) #still not implemented as of Live 8.1.6


    def _on_selected_track_changed(self):
        ControlSurface._on_selected_track_changed(self)
        track = self.song().view.selected_track
        device_to_select = track.view.selected_device
        if device_to_select == None and len(track.devices) > 0:
            device_to_select = track.devices[0]
        if device_to_select != None:
            self.song().view.select_device(device_to_select)
        self._device_component.set_device(device_to_select)


    def _load_pad_translations(self):
        if -1 not in DRUM_PADS:
            pad = []
            for row in range(4):
                for col in range(4):
                    pad = (col, row, DRUM_PADS[row*4 + col], PADCHANNEL,)
                    self._pads.append(pad)
            self.set_pad_translations(tuple(self._pads))


    def _load_MIDI_map(self):
        is_momentary = True
        for note in range(128):
            button = ButtonElement(is_momentary, MIDI_NOTE_TYPE, BUTTONCHANNEL, note)
            button.name = 'Note_' + str(note)
            self._note_map.append(button)
        self._note_map.append(None)
        for ctrl in range(128):
            control = ButtonElement(is_momentary, MIDI_CC_TYPE, BUTTONCHANNEL, ctrl)
            control.name = 'Ctrl_' + str(control)
            self._ctrl_map.append(control)
        self._note_map.append(None) #add None to the end of the list, selectable with [-1]
        for ctrl in range(128):
            control = SliderElement(MIDI_CC_TYPE, SLIDERCHANNEL, ctrl)
            control.name = 'Ctrl_' + str(ctrl)
            self._ctrl_map.append(control)
        self._ctrl_map.append(None)
