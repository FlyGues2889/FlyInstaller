## 依赖库

执行以下代码：
```
pip install customtkinter
pip install pathlib
```

## 运行

执行以下代码：
```
python installer.py
```

## 编译

安装 pyinstaller：
```
pip install pyinstaller
```
运行编译：
```
python -m PyInstaller -F -w -i "install.ico" --name "FlyInstaller" --add-data "package;package" installer.py
```