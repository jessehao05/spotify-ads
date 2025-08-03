# testing muting and unmuting spotify application

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, ISimpleAudioVolume

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

current = volume.GetMasterVolumeLevel()
print(current)

# SetMute(): 1 for mute, 0 for unmute

sessions = AudioUtilities.GetAllSessions()


for session in sessions:
    volume = session._ctl.QueryInterface(ISimpleAudioVolume)


    # if session.Process:
    #     print(session.Process.name())

    if session.Process and session.Process.name() == "Spotify.exe":
        volume.SetMute(0, None)    
    
