# zsh-toolkit
A collection of bash & python scripts I use as helpers in zsh

# Install
```zsh -c "$(curl -fsSL https://raw.githubusercontent.com/c0d3m0nky/zsh-toolkit/main/install.sh)"```

# ToDo
* Remove global pip dependencies as an option
* Include extra scripts
  * Test shell includes
  * Figure out how to handle python includes and document it
* Separate and cache of heuristics
* Troubleshoot and optimize load times
* Prevent changes to pack from being committed without updating version
* Add oh-my-zsh to install script
* Expand magicFiles.sh to all
* Write tests
  * magicfiles.sh and magic_files.py are in sync
  * Each py pack applet
* Add to install script
  * Check for zsh
  * Check for python3.12+
  * Check/install python-env
  * Check/install pip
  * Check/install pipx
  * Check for ack
  * Check/install oh-my-zsh
  * Ask for needed customizations
  * Setup https://github.com/romkatv/powerlevel10k
    * ask to install
    * make it a script that can be run afterwards
    * install fonts locally
    * set default .p10k.zsh
    * swap out theme and add source to .zshrc
  
