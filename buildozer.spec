[app]
title = Nexopraim
package.name = nexopraim
package.domain = org.nexopraim
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow,websockets,asyncio,openssl,requests,urllib3,charset-normalizer,idna,certifi
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 33
android.minapi = 24
android.ndk = 25c
android.archs = arm64-v8a
android.allow_backup = True
p4a.branch = master
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
