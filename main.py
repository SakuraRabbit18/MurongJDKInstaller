import os, PyQt5
import shutil
import sys  # 导入sys模块，用于访问系统特定的参数和函数
import json
import tarfile
import re
import time
import platform
import warnings  # 导入warnings模块，用于处理警告信息
warnings.filterwarnings("ignore", category=DeprecationWarning)  # 忽略DeprecationWarning警告
import ctypes


from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QProgressBar, \
    QMessageBox, QFrame, QLabel, QFileDialog, QTextEdit, QDesktopWidget  # 从PyQt5.QtWidgets模块导入所需的类
from PyQt5.QtCore import QThread, pyqtSlot, pyqtSignal, Qt  # 从PyQt5.QtCore模块导入QThread类
from qt_material import apply_stylesheet

# 获取PyQt5的安装路径
dirname = os.path.dirname(PyQt5.__file__)
# 获取Qt5的插件路径
qt_dir = os.path.join(dirname, 'Qt5', 'plugins', 'platforms')
# 设置环境变量，指定Qt5的插件路径
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_dir
if platform.system() == "Windows":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid") #任务栏图标

class Config():
    def __init__(self):
        with open('config.json', 'r') as f:
            self.config = json.load(f)
        self.jdk_linux_path = self.config['jdk_linux_path']
        self.jdk_windows_path = self.config['jdk_windows_path']
        self.jdk_env_var_name = self.config['jdk_env_var_name']
        self.installed_jdk_path = self.config['installed_jdk_path']
        self.root_dir = self.config['root_dir']
        self.linux_root_dir = self.config['linux_root_dir']
        self.windows_root_dir = self.config['windows_root_dir']

    def dump_config(self):
        with open('config.json', 'w') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

# 定义JavaInstallerGUI类，继承自QWidget
class JavaInstallerGUI(QWidget):
    def __init__(self):
        super().__init__()  # 调用父类的构造函数
        self.direction = None  # 调整方向
        self.right_edge = None  # 右边缘
        self.bottom_edge = None  # 下边缘
        self.right_bottom_edge = None  # 右下边缘
        try:
            self.config = Config()
        except:
            QMessageBox.warning(self, "警告", "请检查config.json文件是否和程序在同一目录下，并且格式正确。")
            sys.exit()
        self.tar_file = ""
        self.unziped_jdk_full_path = None
        self.initUI()  # 调用初始化UI界面的方法

    # 初始化UI界面
    def initUI(self):
        self.setWindowTitle('Java Installer')  # 设置窗口标题

        self.progress_bar = QProgressBar(self)  # 创建一个进度条，用于显示安装进度
        self.info_edit = QTextEdit(self)  # 进度条下面的文本框，用于显示详细信息
        self.info_edit.setReadOnly(True)  # 设置文本框为只读模式
        self.root_dir_label = QLabel("选择安装目录:", self)
        self.root_dir_label.setStyleSheet("QLabel { color: #4dd0e1; }")
        self.root_dir_edit = QLineEdit(self)  # 创建一个文本框，用于输入安装路径
        self.root_dir_edit.setStyleSheet("QLineEdit { color: #4dd0e1; }")
        self.select_root_dir_button = QPushButton("选择", self)  # 选择路径按钮
        self.select_root_dir_button.clicked.connect(self.select_root_dir)

        self.install_button_8 = QPushButton('安装 JDK 8', self)  # 创建一个按钮，用于安装JDK 8
        self.switch_button_8 = QPushButton('切换到 JDK 8', self)  # 创建一个按钮，用于切换到JDK 8
        self.install_button_11 = QPushButton('安装 JDK 11', self)  # 创建一个按钮，用于安装JDK 11
        self.switch_button_11 = QPushButton('切换到 JDK 11', self)  # 创建一个按钮，用于切换到JDK 11
        self.install_button_17 = QPushButton('安装 JDK 17', self)  # 创建一个按钮，用于安装JDK 17
        self.switch_button_17 = QPushButton('切换到 JDK 17', self)  # 创建一个按钮，用于切换到JDK 17
        self.install_button_21 = QPushButton('安装 JDK 21', self)  # 创建一个按钮，用于安装JDK 21
        self.switch_button_21 = QPushButton('切换到 JDK 21', self)  # 创建一个按钮，用于切换到JDK 21

        self.add_path_button = QPushButton('添加JAVA_HOME\\BIN到PATH(命令行中不能运行点我一次)', self)  # 创建一个按钮，用于切换到JDK 21

        install_layout = QVBoxLayout()  # 创建一个垂直布局，用于放置安装按钮
        install_layout.addWidget(self.install_button_8)  # 添加安装JDK 8按钮
        install_layout.addWidget(self.install_button_11)  # 添加安装JDK 11按钮
        install_layout.addWidget(self.install_button_17)  # 添加安装JDK 17按钮
        install_layout.addWidget(self.install_button_21)  # 添加安装JDK 21按钮

        switch_layout = QVBoxLayout()  # 创建一个垂直布局，用于放置切换按钮
        switch_layout.addWidget(self.switch_button_8)  # 添加切换到JDK 8按钮
        switch_layout.addWidget(self.switch_button_11)  # 添加切换到JDK 11按钮
        switch_layout.addWidget(self.switch_button_17)  # 添加切换到JDK 17按钮
        switch_layout.addWidget(self.switch_button_21)  # 添加切换到JDK 21按钮

        root_dir_layout = QHBoxLayout()  # 水平布局，用于选择安装路径
        root_dir_layout.addWidget(self.root_dir_label)
        root_dir_layout.addWidget(self.root_dir_edit)
        root_dir_layout.addWidget(self.select_root_dir_button)

        main_layout = QHBoxLayout()  # 创建一个水平布局，用于放置安装和切换布局
        main_layout.addLayout(install_layout)  # 添加安装布局
        main_layout.addLayout(switch_layout)  # 添加切换布局

        layout = QVBoxLayout()  # 创建一个垂直布局，用于放置所有布局
        layout.addStretch(1)
        layout.addLayout(root_dir_layout)  # 添加安装路径文本框
        layout.addStretch(1)  # 添加一个拉伸因子，使安装路径文本框占据剩余的空间
        layout.addLayout(main_layout)  # 添加安装和切换布局
        layout.addWidget(self.add_path_button)
        layout.addStretch(1)  # 添加一个拉伸因子，使安装和切换布局占据剩余的空间的2倍
        layout.addWidget(self.progress_bar)  # 添加进度条
        layout.addWidget(self.info_edit)  # 添加详细安装信息文本框
        layout.addStretch(1)  # 添加一个拉伸因子，使详细安装信息文本框占据剩余的空间

        self.setLayout(layout)  # 设置窗口的布局

        # 根据操作系统设置默认安装路径
        if platform.system() == "Windows":
            self.root_dir_edit.setText(self.config.windows_root_dir)  # 设置Windows系统的默认安装路径
        else:
            self.root_dir_edit.setText(self.config.linux_root_dir)  # 设置Linux系统的默认安装路径

        # 连接按钮的点击事件

        self.install_button_8.clicked.connect(lambda: self.start_install('8'))  # 连接安装JDK 8按钮的点击事件
        self.switch_button_8.clicked.connect(lambda: self.switch_jdk('8'))  # 连接切换到JDK 8按钮的点击事件
        self.install_button_11.clicked.connect(lambda: self.start_install('11'))  # 连接安装JDK 11按钮的点击事件
        self.switch_button_11.clicked.connect(lambda: self.switch_jdk('11'))  # 连接切换到JDK 11按钮的点击事件
        self.install_button_17.clicked.connect(lambda: self.start_install('17'))  # 连接安装JDK 17按钮的点击事件
        self.switch_button_17.clicked.connect(lambda: self.switch_jdk('17'))  # 连接切换到JDK 17按钮的点击事件
        self.install_button_21.clicked.connect(lambda: self.start_install('21'))  # 连接安装JDK 21按钮的点击事件
        self.switch_button_21.clicked.connect(lambda: self.switch_jdk('21'))  # 连接切换到JDK 21按钮的点击事件

        self.add_path_button.clicked.connect(self.add_path)  # 连接添加环境变量按钮的点击事件

    def add_path(self):
        if platform.system() == "Windows":
            cmd = 'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v "Path" /t REG_EXPAND_SZ /d "%PATH%"%"JAVA_HOME"%\\bin /f'
            os.system(cmd)
            self.info_edit.append(f"[+]执行命令: {cmd}")
            self.info_edit.append(f"[+] 写入: PATH" + " = " + "%PATH%;%JAVA_HOME%\\bin")
        else:
            default_shell = os.environ.get('SHELL')
            # 不同系统不同shell，配置文件不同
            if "bash" in default_shell:
                config_file = "/etc/profile"
            else:
                config_file = "/etc/zsh/zshrc"
            # PATH一定要在JAVA_HOME之后，所以进行覆写
            self.avoid_dup_PATH(config_file)
            self.set_environment_variable("PATH", "${JAVA_HOME}/bin:$PATH")
            self.info_edit.append(f"[+] 写入: PATH" + " = " + "${JAVA_HOME}/bin:$PATH")

    # 开始安装
    def start_install(self, version):
        try:
            is_installed = self.config.installed_jdk_path.get(version, "uninstall")
            if (is_installed != "uninstall"):
                QMessageBox.information(self, "提示", f"JDK {version} 已经安装，无需重复安装")
            else:
                self.base_path = os.path.normpath(os.path.join(self.root_dir_edit.text()))
                self.info_edit.append(f"[+]JDK安装的根目录为: {self.base_path}")
                if not os.path.exists(self.base_path):
                    os.makedirs(self.base_path)
                # 根据操作系统设置默认安装路径
                if platform.system() == "Windows":
                    self.tar_file = self.config.jdk_windows_path[version]
                else:
                    try:
                        self.tar_file = self.config.jdk_linux_path[version]
                    except Exception as e:
                        QMessageBox.warning(self, "警告", f"请检查JDK安装包配置是否正确,错误信息: {e}")
                try:
                    self.unzip_file(version)
                    self.set_environment(version,self.config.installed_jdk_path[version])
                    self.info_edit.append("[+]配置环境变量完成")
                except FileNotFoundError:
                    QMessageBox.warning(self, "警告", "请检查JDK安装包配置是否正确")
                except Exception as e:
                    QMessageBox.warning(self, "警告", f"发生错误: {e}")
                else:
                    self.finished_installing()
        except KeyError as e:
            QMessageBox.warning(self, "警告", f"JDK目录下没有JDK{version}版本安装包，请下载并放到JDK目录下，并检查config.json配置无误")

    def unzip_file(self, version):
        self.progress_bar.setMaximum(0)
        self.progress_bar.setValue(0)
        # 打开tar文件
        with tarfile.open(self.tar_file, 'r') as tar_ref:
            # 解压后文件的根目录
            unziped_file__root = re.split(r"[\\/]", tar_ref.getnames()[0])[0]
            # 解压后JDK的绝对路径
            self.unziped_jdk_full_path = os.path.join(self.base_path, unziped_file__root)
            # 获取所有文件的大小总和
            total_size = sum(member.size for member in tar_ref.getmembers())
            current_size = 0
            # 设置进度条的最大值
            self.progress_bar.setMaximum(total_size)
            self.info_edit.append(f"[+]开始安装: JDK{version}")
            # 遍历tar中的所有文件并解压
            for member in tar_ref:
                file_path = os.path.normpath(os.path.join(self.base_path, member.name))
                self.info_edit.append(file_path)
                # 解压文件
                tar_ref.extract(member, path=self.base_path)
                current_size += member.size
                self.progress_bar.setValue(current_size)
            self.info_edit.append(f"[+]JDK{version}成功安装到: {self.unziped_jdk_full_path}")
        # 解压完成后更新进度条
        self.progress_bar.setValue(self.progress_bar.maximum())
        # 已经安装的JDK写入配置文件
        self.config.installed_jdk_path[version] = os.path.normpath(self.unziped_jdk_full_path)
        # 保存配置文件
        self.config.dump_config()
        self.info_edit.append("[+]开始配置环境变量，可能会卡住，请等待一段时间....")
        time.sleep(1)

    # 更新进度条
    def update_progress(self, value):
        self.progress_bar.setValue(value)  # 更新进度条的值

    # 安装完成
    def finished_installing(self):

        QMessageBox.information(self, '提示', '安装完成')  # 显示安装完成的提示消息

    # 切换JDK版本
    def switch_jdk(self, version):
        installed = self.config.installed_jdk_path.get(version,None)
        if installed is not None:
            self.info_edit.append(f"[+] 正在切换到JDK {version}，这需要一段时间，请等待...")
            time.sleep(1)
            if platform.system() == "Windows":
                self.set_environment_variable("JAVA_HOME", f"^%JAVA_HOME{version}^%")
            else:
                # 避免重复写入环境变量文件
                default_shell = os.environ.get('SHELL')
                # 不同系统不同shell，配置文件不同
                if "bash" in default_shell:
                    config_file = "/etc/profile"
                else:
                    config_file = "/etc/zsh/zshrc"
                self.avoid_dup_JAVA_HOME(config_file)
                self.set_environment_variable("JAVA_HOME", "${JAVA_HOME"+str(version) + "}")
                # PATH一定要在JAVA_HOME之后，所以进行覆写
                self.avoid_dup_PATH(config_file)
                self.set_environment_variable("PATH", "${JAVA_HOME}/bin:$PATH")
            QMessageBox.information(self, '提示', f'已经切换到JDK {version}.')  # 显示切换JDK版本的提示消息
            self.info_edit.append(f"[+] 切换到JDK {version}")
        else:
            QMessageBox.warning(self, '警告', f'还未安装JDK {version}，请先点击左侧安装')  # 显示切换JDK版本的提示消息

    def set_environment_variable(self, key, value):
        if platform.system() == "Windows":
            os.system(f"setx /M {key} {value}")
            self.info_edit.append("[+]执行命令: " f"setx /M {key} {value}")
        elif platform.system() == "Linux":
            default_shell = os.environ.get('SHELL')
            if "bash" in default_shell:
                config_file = "/etc/profile"
            # Linux 设置方法
            else:
                config_file = "/etc/zsh/zshrc"
            with open(config_file, 'a') as f:
                f.write(f"export {key}={value}\n")
            self.info_edit.append(f"[+]写入: {config_file}: export {key}={value}")
            if "bash" in default_shell:
                os.system(f'bash -c "source {config_file}"')
            # Linux 设置方法
            else:
                os.system(f'zsh -c "source {config_file}"')
            self.info_edit.append("[+]执行: " + "source " + config_file)

    def set_environment(self,version, jdk_install_path):
        current_path = os.environ.get('PATH')
        if platform.system() == "Windows":
            # 设置具体的JAVA_HOME版本
            self.set_environment_variable(f"JAVA_HOME{version}", jdk_install_path)
            self.info_edit.append(f"[+] 写入: JAVA_HOME{version}" + " = " + jdk_install_path)
            self.set_environment_variable("JAVA_HOME", f"^%JAVA_HOME{version}^%")
            self.info_edit.append(f"[+] 写入: JAVA_HOME" + " = " + f"%JAVA_HOME{version}%")
            self.set_environment_variable("CLASSPATH", ".;^%JAVA_HOME^%\\lib;^%JAVA_HOME^%\\lib\\tools.jar")
            self.info_edit.append(f"[+] 写入: CLASSPATH" + " = " + ".;%JAVA_HOME%\\lib;%JAVA_HOME%\\lib\\tools.jar")
            pattern = r'jdk.*\\bin'
            match = re.search(pattern, current_path)
            if match:
                self.info_edit.append("[+]匹配到JDK已经在PATH路径，无需写入PATH")
            else:
                self.set_environment_variable("PATH", "%PATH%;^%JAVA_HOME^%\\bin")
                self.info_edit.append(f"[+] 写入: PATH" + " = " + "%PATH%;%JAVA_HOME%\\bin")
        else:
            # 避免重复写入环境变量文件
            default_shell = os.environ.get('SHELL')
            # 不同系统不同shell，配置文件不同
            if "bash" in default_shell:
                config_file = "/etc/profile"
            else:
                config_file = "/etc/zsh/zshrc"
            self.avoid_dup_linux_env_var(config_file, version)
            # 设置具体的JAVA_HOME版本
            self.set_environment_variable(f"JAVA_HOME{version}", jdk_install_path)
            self.info_edit.append(f"[+]写入: JAVA_HOME{version}" + " = " + jdk_install_path)
            self.set_environment_variable("JAVA_HOME", "${JAVA_HOME"+str(version) + "}")
            self.info_edit.append(f"[+]写入: JAVA_HOME" + " = " + "${JAVA_HOME"+str(version) + "}")
            self.set_environment_variable("CLASSPATH", ".:${JAVA_HOME}/jre/lib/rt.jar:${JAVA_HOME}/lib/dt.jar:${JAVA_HOME}/lib/tools.jar:${JAVA_HOME}/lib")
            self.info_edit.append(f"[+]写入: CLASSPATH" + " = " + ".:${JAVA_HOME}/jre/lib/rt.jar:${JAVA_HOME}/lib/dt.jar:${JAVA_HOME}/lib/tools.jar:${JAVA_HOME}/lib")
            pattern = r'jdk.*/bin'
            match = re.search(pattern, current_path)
            if match:
                self.info_edit.append("[+]匹配到JDK已经在PATH路径，无需写入PATH")
            else:
                self.set_environment_variable("PATH", "${JAVA_HOME}/bin:$PATH")
                self.info_edit.append(f"[+]写入: PATH" + " = " + "$PATH:$JAVA_HOME/bin")
    # 避免每次都写入环境变量文件，造成重复
    def avoid_dup_linux_env_var(self, env_file,version):
        # 定义要匹配的模式
        patterns_to_delete = [
            r'^export JAVA_HOME=.*',
            r'^export JAVA_HOME' + str(version) + '=.*',
            r'^export CLASSPATH=.*',
            r'^export PATH=\$\{JAVA_HOME\}/bin:\$PATH'
        ]

        # 原始文件路径
        original_file_path = env_file
        # 备份文件路径
        backup_file_path = f'{env_file}.backup'
        # 备份原始文件，如果备份文件已存在则覆盖
        if os.path.exists(backup_file_path):
            os.remove(backup_file_path)  # 删除已存在的备份文件
        # 复制原始文件到备份文件
        shutil.copyfile(original_file_path, backup_file_path)
        # 读取文件内容
        with open(original_file_path, 'r') as file:
            lines = file.readlines()
        # 新的内容列表，排除匹配上述模式的行
        new_lines = [
            line for line in lines
            if not any(re.match(pattern, line) for pattern in patterns_to_delete)
        ]
        # 将新内容写回文件
        with open(original_file_path, 'w') as file:
            file.writelines(new_lines)
        #print(f"已删除匹配以下模式的行：\n{', '.join(patterns_to_delete)}")

    def avoid_dup_JAVA_HOME(self,env_file):
        # 定义要匹配的模式
        patterns_to_delete = [
            r'^export JAVA_HOME=.*',
        ]
        # 原始文件路径
        original_file_path = env_file
        # 备份文件路径
        backup_file_path = f'{env_file}.backup'
        # 备份原始文件，如果备份文件已存在则覆盖
        if os.path.exists(backup_file_path):
            os.remove(backup_file_path)  # 删除已存在的备份文件
        # 复制原始文件到备份文件
        shutil.copyfile(original_file_path, backup_file_path)
        # 读取文件内容
        with open(original_file_path, 'r') as file:
            lines = file.readlines()
        # 新的内容列表，排除匹配上述模式的行
        new_lines = [
            line for line in lines
            if not any(re.match(pattern, line) for pattern in patterns_to_delete)
        ]
        # 将新内容写回文件
        with open(original_file_path, 'w') as file:
            file.writelines(new_lines)
        #print(f"已删除匹配以下模式的行：\n{', '.join(patterns_to_delete)}")

    def avoid_dup_PATH(self,env_file):
        # 定义要匹配的模式
        patterns_to_delete = [
            r'^export PATH=\$\{JAVA_HOME\}/bin:\$PATH',
        ]
        # 原始文件路径
        original_file_path = env_file
        # 备份文件路径
        backup_file_path = f'{env_file}.backup'
        # 备份原始文件，如果备份文件已存在则覆盖
        if os.path.exists(backup_file_path):
            os.remove(backup_file_path)  # 删除已存在的备份文件
        # 复制原始文件到备份文件
        shutil.copyfile(original_file_path, backup_file_path)
        # 读取文件内容
        with open(original_file_path, 'r') as file:
            lines = file.readlines()
        # 新的内容列表，排除匹配上述模式的行
        new_lines = [
            line for line in lines
            if not any(re.match(pattern, line) for pattern in patterns_to_delete)
        ]
        # 将新内容写回文件
        with open(original_file_path, 'w') as file:
            file.writelines(new_lines)
        #print(f"已删除匹配以下模式的行：\n{', '.join(patterns_to_delete)}")
    # 鼠标按下事件
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    # 鼠标移动事件
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def toggle_hide(self):
        """
        切换窗口的显示和隐藏
        """
        if self.isVisible():
            self.hide()
        else:
            self.show()

    # 选择安装路径
    def select_root_dir(self):
        root_dir = QFileDialog.getExistingDirectory(self, 'Select Installation Directory')  # 打开文件对话框，选择安装路径
        if root_dir:  # 如果选择了路径
            self.root_dir_edit.setText(root_dir)  # 设置安装路径文本框的文本为选择的路径



if __name__ == '__main__':
    app = QApplication(sys.argv)  # 创建一个QApplication对象
    ex = JavaInstallerGUI()  # 创建一个JavaInstallerGUI对象
    apply_stylesheet(app, theme='dark_cyan.xml')

    # 获取屏幕的大小
    screen = QDesktopWidget().screenGeometry()
    # 设置窗口的大小和位置
    ex.setGeometry(int(screen.width() * 0.25), int(screen.height() * 0.25), int(screen.width() * 0.5),
                   int(screen.height() * 0.5))

    # 去除系统提供的窗口边框
    ex.setWindowFlags(Qt.FramelessWindowHint)
    ex.setStyleSheet("font-size: 25px;")

    # 创建自定义的窗口边框
    frame = QFrame(ex)
    frame.setFrameShape(QFrame.Box)
    frame.setFrameShadow(QFrame.Sunken)
    frame.setStyleSheet("background-color: #333333; color: #ffffff;")
    frame.setGeometry(0, 0, ex.width(), 30)

    # 创建标题标签
    title_label = QLabel("慕蓉JDK全平台一键安装器v1.0 By 云隐安全",frame)
    title_label.adjustSize()
    title_label.setStyleSheet("color: #ffffff; background-color: transparent;")
    #title_label.setGeometry(10, 0, 400, 30)

    # 创建关闭按钮
    close_button = QPushButton("X",frame)
    close_button.setGeometry(ex.width() - 40, 0, 40, 30)
    close_button.clicked.connect(ex.close)
    close_button.setStyleSheet("background-color: #333333; color: #ffffff;")
    close_button.setStyleSheet("font-size: 10px;")

    hide_button = QPushButton("-",frame)
    hide_button.setGeometry(ex.width() - 80, 0, 40, 30)  # 位置和大小
    hide_button.clicked.connect(ex.showMinimized)  # 连接隐藏功能
    hide_button.setStyleSheet("background-color: #333333; color: #ffffff;")

    ex.setWindowIcon(QIcon("./logo2.png"))

    ex.show()  # 显示窗口
    sys.exit(app.exec_())  # 进入应用程序的主循环
