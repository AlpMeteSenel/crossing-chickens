"""Validated, durable LED creative-effect settings and two-colour themes."""
import re
THEMES={
 'ocean':('#00b8ff','#7e4bff'),'neon':('#ff2e88','#2de2e6'),
 'sunset':('#ff7a18','#e52e71'),'forest':('#38e870','#ffd166'),
 'ice':('#90edff','#316cff')}
DEFAULT={'theme':'ocean','primary':'#00b8ff','secondary':'#7e4bff','speed':100,'wave_width':6}
KEYS={'led_theme':'theme','led_primary':'primary','led_secondary':'secondary','led_speed':'speed','led_wave_width':'wave_width'}
def validate_effects(old,data):
 result=dict(old)
 for request,key in KEYS.items():
  if request not in data:continue
  value=data[request]
  if key=='theme':
   if value not in (*THEMES,'custom'):raise ValueError('Unknown LED theme')
  elif key in ('primary','secondary'):
   if not isinstance(value,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',value):raise ValueError('LED colours need #RRGGBB')
   value=value.lower()
  elif type(value) is not int or not (25<=value<=200 if key=='speed' else 1<=value<=15):
   raise ValueError('LED speed needs 25–200%; wave width needs 1–15 LEDs')
  result[key]=value
 if 'led_theme' in data and result['theme'] in THEMES:
  result['primary'],result['secondary']=THEMES[result['theme']]
 if 'led_primary' in data or 'led_secondary' in data:result['theme']='custom'
 return result

def rpc_args(settings):
 return (int(settings['primary'][1:],16),int(settings['secondary'][1:],16),settings['speed'],settings['wave_width'])


def restore_effects(saved):
 """Restore a validated snapshot without treating its saved colours as user edits."""
 result=validate_effects(DEFAULT,{request:saved[key] for request,key in KEYS.items() if key!='theme' and key in saved})
 theme=saved.get('theme',DEFAULT['theme'])
 if theme not in (*THEMES,'custom'):raise ValueError('Unknown saved LED theme')
 if theme in THEMES and (result['primary'],result['secondary'])==THEMES[theme]:result['theme']=theme
 else:result['theme']='custom'
 return result
