/********************************************************************************
** Form generated from reading UI file 'mainTCSTUK.ui'
**
** Created by: Qt User Interface Compiler version 6.2.4
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef MAINTCSTUK_H
#define MAINTCSTUK_H

#include <QtCore/QVariant>
#include <QtGui/QAction>
#include <QtWidgets/QApplication>
#include <QtWidgets/QCheckBox>
#include <QtWidgets/QFrame>
#include <QtWidgets/QGroupBox>
#include <QtWidgets/QHBoxLayout>
#include <QtWidgets/QLabel>
#include <QtWidgets/QListWidget>
#include <QtWidgets/QMainWindow>
#include <QtWidgets/QMenu>
#include <QtWidgets/QMenuBar>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QRadioButton>
#include <QtWidgets/QScrollArea>
#include <QtWidgets/QSpacerItem>
#include <QtWidgets/QSpinBox>
#include <QtWidgets/QStatusBar>
#include <QtWidgets/QVBoxLayout>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_MainWindow
{
public:
    QAction *actionSave;
    QAction *actionSave_as;
    QAction *actionExis;
    QAction *actionExit;
    QAction *actionOpen;
    QAction *actionOpenDB;
    QWidget *centralwidget;
    QVBoxLayout *verticalLayout;
    QSpacerItem *verticalSpacer;
    QGroupBox *gbWorld;
    QHBoxLayout *horizontalLayout_2;
    QScrollArea *scrollArea;
    QWidget *scrollAreaWidgetContents;
    QHBoxLayout *horizontalLayout_3;
    QFrame *frame_3;
    QHBoxLayout *horizontalLayout_4;
    QHBoxLayout *horizontalLayout;
    QHBoxLayout *horizontalLayout_11;
    QListWidget *lstwWorldMainCategory;
    QListWidget *lstwWorldSubCategory;
    QLabel *lbWorldImage;
    QVBoxLayout *verticalLayout_4;
    QGroupBox *groupBox_5;
    QVBoxLayout *verticalLayout_5;
    QVBoxLayout *verticalLayout_3;
    QFrame *frame;
    QHBoxLayout *horizontalLayout_14;
    QHBoxLayout *horizontalLayout_10;
    QHBoxLayout *horizontalLayout_18;
    QCheckBox *chkWorldOptionPerson;
    QLabel *label;
    QSpinBox *sbWorldOptionPersonCount;
    QHBoxLayout *horizontalLayout_19;
    QLabel *lbRandomColor;
    QCheckBox *chkWorldOptionRandomColor;
    QFrame *frame_2;
    QHBoxLayout *horizontalLayout_15;
    QHBoxLayout *horizontalLayout_13;
    QHBoxLayout *horizontalLayout_16;
    QLabel *label_3;
    QHBoxLayout *horizontalLayout_17;
    QLabel *label_2;
    QCheckBox *checkBox;
    QSpacerItem *verticalSpacer_4;
    QSpacerItem *verticalSpacer_2;
    QFrame *frame_19;
    QHBoxLayout *horizontalLayout_29;
    QGroupBox *gbRobot;
    QVBoxLayout *verticalLayout_7;
    QFrame *frame_21;
    QHBoxLayout *horizontalLayout_12;
    QPushButton *btnAddRobot;
    QPushButton *btnDeleteRobot;
    QSpacerItem *horizontalSpacer_2;
    QPushButton *btnAddModel;
    QFrame *frame_8;
    QVBoxLayout *verticalLayout_2;
    QListWidget *lstwRobots;
    QGroupBox *gbRobotROS;
    QVBoxLayout *verticalLayout_19;
    QScrollArea *scrollArea_9;
    QWidget *scrollAreaWidgetContents_9;
    QVBoxLayout *verticalLayout_21;
    QFrame *frame_20;
    QVBoxLayout *verticalLayout_30;
    QGroupBox *gbRobotROSControl;
    QVBoxLayout *verticalLayout_6;
    QVBoxLayout *verticalLayout_8;
    QPushButton *btnROSTeleop;
    QGroupBox *gbRobotROSNavigation;
    QVBoxLayout *verticalLayout_10;
    QVBoxLayout *verticalLayout_9;
    QHBoxLayout *horizontalLayout_9;
    QRadioButton *rbROSNone;
    QHBoxLayout *horizontalLayout_7;
    QRadioButton *rbROSSlam;
    QPushButton *btnROSSlamEdit;
    QHBoxLayout *horizontalLayout_8;
    QRadioButton *rbROSNavigation;
    QPushButton *btnROSNavigationEdit;
    QGroupBox *gbRobotROSJnp;
    QVBoxLayout *verticalLayout_12;
    QVBoxLayout *verticalLayout_11;
    QCheckBox *cbJnpEnable;
    QVBoxLayout *vlJnp;
    QCheckBox *cbJnpOptionTerminal;
    QSpacerItem *verticalSpacer_3;
    QFrame *frame_4;
    QHBoxLayout *horizontalLayout_6;
    QHBoxLayout *horizontalLayout_5;
    QSpacerItem *horizontalSpacer;
    QPushButton *btnStartSimulator;
    QMenuBar *menubar;
    QMenu *menuFIle;
    QMenu *menuDB;
    QStatusBar *statusbar;

    void setupUi(QMainWindow *MainWindow)
    {
        if (MainWindow->objectName().isEmpty())
            MainWindow->setObjectName(QString::fromUtf8("MainWindow"));
        MainWindow->setEnabled(true);
        MainWindow->resize(1135, 1018);
        MainWindow->setMinimumSize(QSize(0, 0));
        actionSave = new QAction(MainWindow);
        actionSave->setObjectName(QString::fromUtf8("actionSave"));
        actionSave_as = new QAction(MainWindow);
        actionSave_as->setObjectName(QString::fromUtf8("actionSave_as"));
        actionExis = new QAction(MainWindow);
        actionExis->setObjectName(QString::fromUtf8("actionExis"));
        actionExit = new QAction(MainWindow);
        actionExit->setObjectName(QString::fromUtf8("actionExit"));
        actionOpen = new QAction(MainWindow);
        actionOpen->setObjectName(QString::fromUtf8("actionOpen"));
        actionOpenDB = new QAction(MainWindow);
        actionOpenDB->setObjectName(QString::fromUtf8("actionOpenDB"));
        centralwidget = new QWidget(MainWindow);
        centralwidget->setObjectName(QString::fromUtf8("centralwidget"));
        centralwidget->setAutoFillBackground(false);
        centralwidget->setStyleSheet(QString::fromUtf8("background-color: gray;"));
        verticalLayout = new QVBoxLayout(centralwidget);
        verticalLayout->setObjectName(QString::fromUtf8("verticalLayout"));
        verticalLayout->setContentsMargins(-1, 0, -1, 0);
        verticalSpacer = new QSpacerItem(20, 20, QSizePolicy::Minimum, QSizePolicy::Fixed);

        verticalLayout->addItem(verticalSpacer);

        gbWorld = new QGroupBox(centralwidget);
        gbWorld->setObjectName(QString::fromUtf8("gbWorld"));
        QSizePolicy sizePolicy(QSizePolicy::Preferred, QSizePolicy::Fixed);
        sizePolicy.setHorizontalStretch(0);
        sizePolicy.setVerticalStretch(0);
        sizePolicy.setHeightForWidth(gbWorld->sizePolicy().hasHeightForWidth());
        gbWorld->setSizePolicy(sizePolicy);
        gbWorld->setMinimumSize(QSize(0, 250));
        gbWorld->setStyleSheet(QString::fromUtf8("QGroupBox#gbWorld {\n"
"    border: 1px solid 	darkgray;\n"
"    background-color: #cccccc;\n"
"    margin-top: 15px;\n"
"    color: white;\n"
"}\n"
"\n"
"QGroupBox#gbWorld::title {\n"
"    border: 1px solid white;\n"
"    subcontrol-position: top left;\n"
"	left: 30px;\n"
"    background-color: gray;\n"
"    padding: 5px 30px 5px 30px;\n"
"    top: -15px;\n"
"}"));
        horizontalLayout_2 = new QHBoxLayout(gbWorld);
        horizontalLayout_2->setSpacing(0);
        horizontalLayout_2->setObjectName(QString::fromUtf8("horizontalLayout_2"));
        horizontalLayout_2->setContentsMargins(10, 20, 10, 10);
        scrollArea = new QScrollArea(gbWorld);
        scrollArea->setObjectName(QString::fromUtf8("scrollArea"));
        scrollArea->setStyleSheet(QString::fromUtf8("background-color: #e6e6e6;\n"
"border-radius:5px;"));
        scrollArea->setWidgetResizable(true);
        scrollAreaWidgetContents = new QWidget();
        scrollAreaWidgetContents->setObjectName(QString::fromUtf8("scrollAreaWidgetContents"));
        scrollAreaWidgetContents->setGeometry(QRect(0, 0, 1095, 214));
        horizontalLayout_3 = new QHBoxLayout(scrollAreaWidgetContents);
        horizontalLayout_3->setSpacing(0);
        horizontalLayout_3->setObjectName(QString::fromUtf8("horizontalLayout_3"));
        horizontalLayout_3->setContentsMargins(0, 0, 0, 0);
        frame_3 = new QFrame(scrollAreaWidgetContents);
        frame_3->setObjectName(QString::fromUtf8("frame_3"));
        frame_3->setStyleSheet(QString::fromUtf8(""));
        frame_3->setFrameShape(QFrame::StyledPanel);
        frame_3->setFrameShadow(QFrame::Raised);
        horizontalLayout_4 = new QHBoxLayout(frame_3);
        horizontalLayout_4->setSpacing(0);
        horizontalLayout_4->setObjectName(QString::fromUtf8("horizontalLayout_4"));
        horizontalLayout_4->setContentsMargins(0, 0, 0, 0);
        horizontalLayout = new QHBoxLayout();
        horizontalLayout->setSpacing(40);
        horizontalLayout->setObjectName(QString::fromUtf8("horizontalLayout"));
        horizontalLayout->setContentsMargins(40, 10, 10, 10);
        horizontalLayout_11 = new QHBoxLayout();
        horizontalLayout_11->setObjectName(QString::fromUtf8("horizontalLayout_11"));
        lstwWorldMainCategory = new QListWidget(frame_3);
        lstwWorldMainCategory->setObjectName(QString::fromUtf8("lstwWorldMainCategory"));
        lstwWorldMainCategory->setStyleSheet(QString::fromUtf8("QListWidget{\n"
"    border: 1px solid 	darkgray;\n"
"    background-color: #cccccc;\n"
"}"));

        horizontalLayout_11->addWidget(lstwWorldMainCategory);

        lstwWorldSubCategory = new QListWidget(frame_3);
        lstwWorldSubCategory->setObjectName(QString::fromUtf8("lstwWorldSubCategory"));
        lstwWorldSubCategory->setStyleSheet(QString::fromUtf8("QListWidget{\n"
"    border: 1px solid 	darkgray;\n"
"    background-color: #cccccc;\n"
"}"));

        horizontalLayout_11->addWidget(lstwWorldSubCategory);

        lbWorldImage = new QLabel(frame_3);
        lbWorldImage->setObjectName(QString::fromUtf8("lbWorldImage"));
        QSizePolicy sizePolicy1(QSizePolicy::Fixed, QSizePolicy::Fixed);
        sizePolicy1.setHorizontalStretch(0);
        sizePolicy1.setVerticalStretch(0);
        sizePolicy1.setHeightForWidth(lbWorldImage->sizePolicy().hasHeightForWidth());
        lbWorldImage->setSizePolicy(sizePolicy1);
        lbWorldImage->setMinimumSize(QSize(300, 180));
        lbWorldImage->setStyleSheet(QString::fromUtf8("QLabel{\n"
"    border: 1px solid 	darkgray;\n"
"    background-color: #cccccc;\n"
"}"));
        lbWorldImage->setScaledContents(false);

        horizontalLayout_11->addWidget(lbWorldImage);


        horizontalLayout->addLayout(horizontalLayout_11);

        verticalLayout_4 = new QVBoxLayout();
        verticalLayout_4->setObjectName(QString::fromUtf8("verticalLayout_4"));
        groupBox_5 = new QGroupBox(frame_3);
        groupBox_5->setObjectName(QString::fromUtf8("groupBox_5"));
        QSizePolicy sizePolicy2(QSizePolicy::Minimum, QSizePolicy::Preferred);
        sizePolicy2.setHorizontalStretch(0);
        sizePolicy2.setVerticalStretch(0);
        sizePolicy2.setHeightForWidth(groupBox_5->sizePolicy().hasHeightForWidth());
        groupBox_5->setSizePolicy(sizePolicy2);
        groupBox_5->setMinimumSize(QSize(300, 0));
        groupBox_5->setStyleSheet(QString::fromUtf8("QGroupBox{\n"
"    border: 1px solid 	darkgray;\n"
"    background-color: #cccccc;\n"
"    margin-top: 15px;\n"
"    color: white;\n"
"}\n"
"\n"
"QGroupBox::title {\n"
"    border: 1px solid white;\n"
"    subcontrol-position: top center;\n"
"    background-color: gray;\n"
"    padding: 5px 30px 5px 30px;\n"
"    top: -15px;\n"
"}"));
        groupBox_5->setFlat(false);
        verticalLayout_5 = new QVBoxLayout(groupBox_5);
        verticalLayout_5->setObjectName(QString::fromUtf8("verticalLayout_5"));
        verticalLayout_5->setContentsMargins(-1, 20, -1, -1);
        verticalLayout_3 = new QVBoxLayout();
        verticalLayout_3->setObjectName(QString::fromUtf8("verticalLayout_3"));
        frame = new QFrame(groupBox_5);
        frame->setObjectName(QString::fromUtf8("frame"));
        sizePolicy.setHeightForWidth(frame->sizePolicy().hasHeightForWidth());
        frame->setSizePolicy(sizePolicy);
        frame->setMinimumSize(QSize(0, 40));
        frame->setFrameShape(QFrame::StyledPanel);
        frame->setFrameShadow(QFrame::Raised);
        horizontalLayout_14 = new QHBoxLayout(frame);
        horizontalLayout_14->setSpacing(0);
        horizontalLayout_14->setObjectName(QString::fromUtf8("horizontalLayout_14"));
        horizontalLayout_14->setContentsMargins(5, 0, 5, 0);
        horizontalLayout_10 = new QHBoxLayout();
        horizontalLayout_10->setSpacing(5);
        horizontalLayout_10->setObjectName(QString::fromUtf8("horizontalLayout_10"));
        horizontalLayout_18 = new QHBoxLayout();
        horizontalLayout_18->setObjectName(QString::fromUtf8("horizontalLayout_18"));
        chkWorldOptionPerson = new QCheckBox(frame);
        chkWorldOptionPerson->setObjectName(QString::fromUtf8("chkWorldOptionPerson"));
        QSizePolicy sizePolicy3(QSizePolicy::Fixed, QSizePolicy::Preferred);
        sizePolicy3.setHorizontalStretch(0);
        sizePolicy3.setVerticalStretch(0);
        sizePolicy3.setHeightForWidth(chkWorldOptionPerson->sizePolicy().hasHeightForWidth());
        chkWorldOptionPerson->setSizePolicy(sizePolicy3);
        chkWorldOptionPerson->setMinimumSize(QSize(0, 0));
        chkWorldOptionPerson->setChecked(false);

        horizontalLayout_18->addWidget(chkWorldOptionPerson);

        label = new QLabel(frame);
        label->setObjectName(QString::fromUtf8("label"));
        label->setStyleSheet(QString::fromUtf8("background-color:transparent;"));

        horizontalLayout_18->addWidget(label);

        sbWorldOptionPersonCount = new QSpinBox(frame);
        sbWorldOptionPersonCount->setObjectName(QString::fromUtf8("sbWorldOptionPersonCount"));
        sbWorldOptionPersonCount->setEnabled(false);
        QSizePolicy sizePolicy4(QSizePolicy::Fixed, QSizePolicy::Expanding);
        sizePolicy4.setHorizontalStretch(0);
        sizePolicy4.setVerticalStretch(0);
        sizePolicy4.setHeightForWidth(sbWorldOptionPersonCount->sizePolicy().hasHeightForWidth());
        sbWorldOptionPersonCount->setSizePolicy(sizePolicy4);
        sbWorldOptionPersonCount->setMinimumSize(QSize(50, 0));
        sbWorldOptionPersonCount->setStyleSheet(QString::fromUtf8("            QSpinBox::up-button {\n"
"                width: 30px;\n"
"            }\n"
"\n"
"            QSpinBox::down-button {\n"
"                width: 30px;\n"
"            }"));
        sbWorldOptionPersonCount->setMinimum(1);
        sbWorldOptionPersonCount->setValue(1);

        horizontalLayout_18->addWidget(sbWorldOptionPersonCount);


        horizontalLayout_10->addLayout(horizontalLayout_18);

        horizontalLayout_19 = new QHBoxLayout();
        horizontalLayout_19->setObjectName(QString::fromUtf8("horizontalLayout_19"));
        lbRandomColor = new QLabel(frame);
        lbRandomColor->setObjectName(QString::fromUtf8("lbRandomColor"));
        lbRandomColor->setAlignment(Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter);

        horizontalLayout_19->addWidget(lbRandomColor);

        chkWorldOptionRandomColor = new QCheckBox(frame);
        chkWorldOptionRandomColor->setObjectName(QString::fromUtf8("chkWorldOptionRandomColor"));
        chkWorldOptionRandomColor->setEnabled(false);
        sizePolicy3.setHeightForWidth(chkWorldOptionRandomColor->sizePolicy().hasHeightForWidth());
        chkWorldOptionRandomColor->setSizePolicy(sizePolicy3);

        horizontalLayout_19->addWidget(chkWorldOptionRandomColor);


        horizontalLayout_10->addLayout(horizontalLayout_19);


        horizontalLayout_14->addLayout(horizontalLayout_10);


        verticalLayout_3->addWidget(frame);

        frame_2 = new QFrame(groupBox_5);
        frame_2->setObjectName(QString::fromUtf8("frame_2"));
        sizePolicy.setHeightForWidth(frame_2->sizePolicy().hasHeightForWidth());
        frame_2->setSizePolicy(sizePolicy);
        frame_2->setMinimumSize(QSize(0, 40));
        frame_2->setFrameShape(QFrame::StyledPanel);
        frame_2->setFrameShadow(QFrame::Raised);
        horizontalLayout_15 = new QHBoxLayout(frame_2);
        horizontalLayout_15->setSpacing(0);
        horizontalLayout_15->setObjectName(QString::fromUtf8("horizontalLayout_15"));
        horizontalLayout_15->setContentsMargins(5, 0, 5, 0);
        horizontalLayout_13 = new QHBoxLayout();
        horizontalLayout_13->setSpacing(5);
        horizontalLayout_13->setObjectName(QString::fromUtf8("horizontalLayout_13"));
        horizontalLayout_16 = new QHBoxLayout();
        horizontalLayout_16->setObjectName(QString::fromUtf8("horizontalLayout_16"));
        label_3 = new QLabel(frame_2);
        label_3->setObjectName(QString::fromUtf8("label_3"));
        label_3->setAlignment(Qt::AlignCenter);

        horizontalLayout_16->addWidget(label_3);


        horizontalLayout_13->addLayout(horizontalLayout_16);

        horizontalLayout_17 = new QHBoxLayout();
        horizontalLayout_17->setObjectName(QString::fromUtf8("horizontalLayout_17"));
        label_2 = new QLabel(frame_2);
        label_2->setObjectName(QString::fromUtf8("label_2"));
        label_2->setAlignment(Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter);

        horizontalLayout_17->addWidget(label_2);

        checkBox = new QCheckBox(frame_2);
        checkBox->setObjectName(QString::fromUtf8("checkBox"));
        checkBox->setEnabled(false);
        sizePolicy3.setHeightForWidth(checkBox->sizePolicy().hasHeightForWidth());
        checkBox->setSizePolicy(sizePolicy3);

        horizontalLayout_17->addWidget(checkBox);


        horizontalLayout_13->addLayout(horizontalLayout_17);


        horizontalLayout_15->addLayout(horizontalLayout_13);


        verticalLayout_3->addWidget(frame_2);

        verticalSpacer_4 = new QSpacerItem(20, 40, QSizePolicy::Minimum, QSizePolicy::Expanding);

        verticalLayout_3->addItem(verticalSpacer_4);


        verticalLayout_5->addLayout(verticalLayout_3);


        verticalLayout_4->addWidget(groupBox_5);


        horizontalLayout->addLayout(verticalLayout_4);


        horizontalLayout_4->addLayout(horizontalLayout);


        horizontalLayout_3->addWidget(frame_3);

        scrollArea->setWidget(scrollAreaWidgetContents);

        horizontalLayout_2->addWidget(scrollArea);


        verticalLayout->addWidget(gbWorld);

        verticalSpacer_2 = new QSpacerItem(20, 20, QSizePolicy::Minimum, QSizePolicy::Fixed);

        verticalLayout->addItem(verticalSpacer_2);

        frame_19 = new QFrame(centralwidget);
        frame_19->setObjectName(QString::fromUtf8("frame_19"));
        frame_19->setFrameShape(QFrame::NoFrame);
        frame_19->setFrameShadow(QFrame::Raised);
        horizontalLayout_29 = new QHBoxLayout(frame_19);
        horizontalLayout_29->setSpacing(20);
        horizontalLayout_29->setObjectName(QString::fromUtf8("horizontalLayout_29"));
        horizontalLayout_29->setContentsMargins(0, 0, 0, 0);
        gbRobot = new QGroupBox(frame_19);
        gbRobot->setObjectName(QString::fromUtf8("gbRobot"));
        gbRobot->setEnabled(true);
        sizePolicy3.setHeightForWidth(gbRobot->sizePolicy().hasHeightForWidth());
        gbRobot->setSizePolicy(sizePolicy3);
        gbRobot->setMinimumSize(QSize(800, 0));
        gbRobot->setLayoutDirection(Qt::LeftToRight);
        gbRobot->setStyleSheet(QString::fromUtf8("QGroupBox#gbRobot{\n"
"    border: 1px solid 	darkgray;\n"
"    background-color: #cccccc;\n"
"    margin-top: 15px;\n"
"    color: white;\n"
"}\n"
"\n"
"QGroupBox#gbRobot::title {\n"
"    border: 1px solid white;\n"
"    background-color: gray;\n"
"    padding: 5px 30px 5px 30px;\n"
"    top: -15px;\n"
"    left: 30px;\n"
"}"));
        verticalLayout_7 = new QVBoxLayout(gbRobot);
        verticalLayout_7->setSpacing(0);
        verticalLayout_7->setObjectName(QString::fromUtf8("verticalLayout_7"));
        verticalLayout_7->setContentsMargins(9, 20, 9, 10);
        frame_21 = new QFrame(gbRobot);
        frame_21->setObjectName(QString::fromUtf8("frame_21"));
        sizePolicy.setHeightForWidth(frame_21->sizePolicy().hasHeightForWidth());
        frame_21->setSizePolicy(sizePolicy);
        frame_21->setMinimumSize(QSize(0, 60));
        frame_21->setFrameShape(QFrame::StyledPanel);
        frame_21->setFrameShadow(QFrame::Raised);
        horizontalLayout_12 = new QHBoxLayout(frame_21);
        horizontalLayout_12->setObjectName(QString::fromUtf8("horizontalLayout_12"));
        horizontalLayout_12->setContentsMargins(9, 0, 9, 0);
        btnAddRobot = new QPushButton(frame_21);
        btnAddRobot->setObjectName(QString::fromUtf8("btnAddRobot"));
        btnAddRobot->setMinimumSize(QSize(94, 40));
        btnAddRobot->setStyleSheet(QString::fromUtf8("QPushButton {\n"
"color: #333;\n"
"border: 2px solid #555;\n"
"border-radius: 4px;\n"
"padding: 5px;\n"
"background: qradialgradient(cx: 0.3, cy: -0.4,\n"
"fx: 0.3, fy: -0.4,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #888);\n"
"min-width: 80px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"background: qradialgradient(cx: 0.3, cy: -0.4,\n"
"fx: 0.3, fy: -0.4,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #bbb);\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"background: qradialgradient(cx: 0.4, cy: -0.1,\n"
"fx: 0.4, fy: -0.1,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #ddd);\n"
"}"));

        horizontalLayout_12->addWidget(btnAddRobot);

        btnDeleteRobot = new QPushButton(frame_21);
        btnDeleteRobot->setObjectName(QString::fromUtf8("btnDeleteRobot"));
        btnDeleteRobot->setMinimumSize(QSize(94, 40));
        btnDeleteRobot->setStyleSheet(QString::fromUtf8("QPushButton {\n"
"color: #333;\n"
"border: 2px solid #555;\n"
"border-radius: 4px;\n"
"padding: 5px;\n"
"background: qradialgradient(cx: 0.3, cy: -0.4,\n"
"fx: 0.3, fy: -0.4,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #888);\n"
"min-width: 80px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"background: qradialgradient(cx: 0.3, cy: -0.4,\n"
"fx: 0.3, fy: -0.4,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #bbb);\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"background: qradialgradient(cx: 0.4, cy: -0.1,\n"
"fx: 0.4, fy: -0.1,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #ddd);\n"
"}"));

        horizontalLayout_12->addWidget(btnDeleteRobot);

        horizontalSpacer_2 = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        horizontalLayout_12->addItem(horizontalSpacer_2);

        btnAddModel = new QPushButton(frame_21);
        btnAddModel->setObjectName(QString::fromUtf8("btnAddModel"));
        btnAddModel->setMinimumSize(QSize(94, 40));
        btnAddModel->setStyleSheet(QString::fromUtf8("QPushButton {\n"
"color: #333;\n"
"border: 2px solid #555;\n"
"border-radius: 4px;\n"
"padding: 5px;\n"
"background: qradialgradient(cx: 0.3, cy: -0.4,\n"
"fx: 0.3, fy: -0.4,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #888);\n"
"min-width: 80px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"background: qradialgradient(cx: 0.3, cy: -0.4,\n"
"fx: 0.3, fy: -0.4,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #bbb);\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"background: qradialgradient(cx: 0.4, cy: -0.1,\n"
"fx: 0.4, fy: -0.1,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #ddd);\n"
"}"));

        horizontalLayout_12->addWidget(btnAddModel);


        verticalLayout_7->addWidget(frame_21);

        frame_8 = new QFrame(gbRobot);
        frame_8->setObjectName(QString::fromUtf8("frame_8"));
        frame_8->setStyleSheet(QString::fromUtf8("background-color:transparent;"));
        frame_8->setFrameShape(QFrame::StyledPanel);
        frame_8->setFrameShadow(QFrame::Raised);
        verticalLayout_2 = new QVBoxLayout(frame_8);
        verticalLayout_2->setObjectName(QString::fromUtf8("verticalLayout_2"));
        verticalLayout_2->setContentsMargins(0, -1, 0, 0);
        lstwRobots = new QListWidget(frame_8);
        lstwRobots->setObjectName(QString::fromUtf8("lstwRobots"));
        lstwRobots->setStyleSheet(QString::fromUtf8("background-color: gray;"));
        lstwRobots->setResizeMode(QListView::Adjust);

        verticalLayout_2->addWidget(lstwRobots);


        verticalLayout_7->addWidget(frame_8);


        horizontalLayout_29->addWidget(gbRobot);

        gbRobotROS = new QGroupBox(frame_19);
        gbRobotROS->setObjectName(QString::fromUtf8("gbRobotROS"));
        gbRobotROS->setStyleSheet(QString::fromUtf8("QGroupBox#gbRobotROS{\n"
"    border: 1px solid 	darkgray;\n"
"    background-color: #cccccc;\n"
"    margin-top: 15px;\n"
"    color: white;\n"
"}\n"
"\n"
"QGroupBox#gbRobotROS::title {\n"
"    border: 1px solid white;\n"
"    subcontrol-position: top center;\n"
"    background-color: gray;\n"
"    padding: 5px 30px 5px 30px;\n"
"    top: -15px;\n"
"}"));
        verticalLayout_19 = new QVBoxLayout(gbRobotROS);
        verticalLayout_19->setSpacing(0);
        verticalLayout_19->setObjectName(QString::fromUtf8("verticalLayout_19"));
        verticalLayout_19->setContentsMargins(-1, 20, 0, 10);
        scrollArea_9 = new QScrollArea(gbRobotROS);
        scrollArea_9->setObjectName(QString::fromUtf8("scrollArea_9"));
        QSizePolicy sizePolicy5(QSizePolicy::Expanding, QSizePolicy::Expanding);
        sizePolicy5.setHorizontalStretch(0);
        sizePolicy5.setVerticalStretch(0);
        sizePolicy5.setHeightForWidth(scrollArea_9->sizePolicy().hasHeightForWidth());
        scrollArea_9->setSizePolicy(sizePolicy5);
        scrollArea_9->setLayoutDirection(Qt::LeftToRight);
        scrollArea_9->setStyleSheet(QString::fromUtf8("background-color:transparent;\n"
"\n"
""));
        scrollArea_9->setWidgetResizable(true);
        scrollArea_9->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignTop);
        scrollAreaWidgetContents_9 = new QWidget();
        scrollAreaWidgetContents_9->setObjectName(QString::fromUtf8("scrollAreaWidgetContents_9"));
        scrollAreaWidgetContents_9->setGeometry(QRect(0, 0, 284, 560));
        verticalLayout_21 = new QVBoxLayout(scrollAreaWidgetContents_9);
        verticalLayout_21->setObjectName(QString::fromUtf8("verticalLayout_21"));
        verticalLayout_21->setSizeConstraint(QLayout::SetDefaultConstraint);
        verticalLayout_21->setContentsMargins(0, -1, -1, -1);
        frame_20 = new QFrame(scrollAreaWidgetContents_9);
        frame_20->setObjectName(QString::fromUtf8("frame_20"));
        frame_20->setStyleSheet(QString::fromUtf8("background-color: #e6e6e6;\n"
"border-radius:5px;"));
        frame_20->setFrameShape(QFrame::StyledPanel);
        frame_20->setFrameShadow(QFrame::Raised);
        verticalLayout_30 = new QVBoxLayout(frame_20);
        verticalLayout_30->setObjectName(QString::fromUtf8("verticalLayout_30"));
        gbRobotROSControl = new QGroupBox(frame_20);
        gbRobotROSControl->setObjectName(QString::fromUtf8("gbRobotROSControl"));
        gbRobotROSControl->setStyleSheet(QString::fromUtf8("QGroupBox#gbRobotROSControl{\n"
"    border: 1px solid 	darkgray;\n"
"    margin-top: 15px;\n"
"	padding-top: 15px;\n"
"    color: white;\n"
"}\n"
"\n"
"QGroupBox#gbRobotROSControl::title {\n"
"    subcontrol-position: top left;\n"
"    border: 1px solid white;\n"
"    background-color: gray;\n"
"    padding: 5px 15px 5px 15px;\n"
"    top: -15px;\n"
"	left: 20px;\n"
"}"));
        verticalLayout_6 = new QVBoxLayout(gbRobotROSControl);
        verticalLayout_6->setObjectName(QString::fromUtf8("verticalLayout_6"));
        verticalLayout_8 = new QVBoxLayout();
        verticalLayout_8->setObjectName(QString::fromUtf8("verticalLayout_8"));
        btnROSTeleop = new QPushButton(gbRobotROSControl);
        btnROSTeleop->setObjectName(QString::fromUtf8("btnROSTeleop"));
        btnROSTeleop->setMinimumSize(QSize(94, 40));
        btnROSTeleop->setStyleSheet(QString::fromUtf8("QPushButton {\n"
"color: #333;\n"
"border: 2px solid #555;\n"
"border-radius: 4px;\n"
"padding: 5px;\n"
"background: qradialgradient(cx: 0.3, cy: -0.4,\n"
"fx: 0.3, fy: -0.4,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #888);\n"
"min-width: 80px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"background: qradialgradient(cx: 0.3, cy: -0.4,\n"
"fx: 0.3, fy: -0.4,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #bbb);\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"background: qradialgradient(cx: 0.4, cy: -0.1,\n"
"fx: 0.4, fy: -0.1,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #ddd);\n"
"}"));

        verticalLayout_8->addWidget(btnROSTeleop);


        verticalLayout_6->addLayout(verticalLayout_8);


        verticalLayout_30->addWidget(gbRobotROSControl);

        gbRobotROSNavigation = new QGroupBox(frame_20);
        gbRobotROSNavigation->setObjectName(QString::fromUtf8("gbRobotROSNavigation"));
        gbRobotROSNavigation->setStyleSheet(QString::fromUtf8("QGroupBox#gbRobotROSNavigation{\n"
"    border: 1px solid 	darkgray;\n"
"    margin-top: 15px;\n"
"	padding-top: 15px;\n"
"    color: white;\n"
"}\n"
"\n"
"QGroupBox#gbRobotROSNavigation::title {\n"
"    subcontrol-position: top left;\n"
"    border: 1px solid white;\n"
"    background-color: gray;\n"
"    padding: 5px 15px 5px 15px;\n"
"    top: -15px;\n"
"	left: 20px;\n"
"}"));
        verticalLayout_10 = new QVBoxLayout(gbRobotROSNavigation);
        verticalLayout_10->setObjectName(QString::fromUtf8("verticalLayout_10"));
        verticalLayout_9 = new QVBoxLayout();
        verticalLayout_9->setObjectName(QString::fromUtf8("verticalLayout_9"));
        horizontalLayout_9 = new QHBoxLayout();
        horizontalLayout_9->setObjectName(QString::fromUtf8("horizontalLayout_9"));
        rbROSNone = new QRadioButton(gbRobotROSNavigation);
        rbROSNone->setObjectName(QString::fromUtf8("rbROSNone"));
        rbROSNone->setMinimumSize(QSize(0, 40));
        rbROSNone->setChecked(true);

        horizontalLayout_9->addWidget(rbROSNone);


        verticalLayout_9->addLayout(horizontalLayout_9);

        horizontalLayout_7 = new QHBoxLayout();
        horizontalLayout_7->setObjectName(QString::fromUtf8("horizontalLayout_7"));
        rbROSSlam = new QRadioButton(gbRobotROSNavigation);
        rbROSSlam->setObjectName(QString::fromUtf8("rbROSSlam"));
        rbROSSlam->setEnabled(false);
        rbROSSlam->setMinimumSize(QSize(0, 40));
        rbROSSlam->setCheckable(false);

        horizontalLayout_7->addWidget(rbROSSlam);

        btnROSSlamEdit = new QPushButton(gbRobotROSNavigation);
        btnROSSlamEdit->setObjectName(QString::fromUtf8("btnROSSlamEdit"));
        sizePolicy1.setHeightForWidth(btnROSSlamEdit->sizePolicy().hasHeightForWidth());
        btnROSSlamEdit->setSizePolicy(sizePolicy1);
        btnROSSlamEdit->setMinimumSize(QSize(94, 0));
        btnROSSlamEdit->setStyleSheet(QString::fromUtf8("QPushButton {\n"
"color: #333;\n"
"border: 2px solid #555;\n"
"border-radius: 4px;\n"
"padding: 5px;\n"
"background: qradialgradient(cx: 0.3, cy: -0.4,\n"
"fx: 0.3, fy: -0.4,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #888);\n"
"min-width: 80px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"background: qradialgradient(cx: 0.3, cy: -0.4,\n"
"fx: 0.3, fy: -0.4,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #bbb);\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"background: qradialgradient(cx: 0.4, cy: -0.1,\n"
"fx: 0.4, fy: -0.1,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #ddd);\n"
"}"));

        horizontalLayout_7->addWidget(btnROSSlamEdit);

        horizontalLayout_7->setStretch(0, 1);

        verticalLayout_9->addLayout(horizontalLayout_7);

        horizontalLayout_8 = new QHBoxLayout();
        horizontalLayout_8->setObjectName(QString::fromUtf8("horizontalLayout_8"));
        rbROSNavigation = new QRadioButton(gbRobotROSNavigation);
        rbROSNavigation->setObjectName(QString::fromUtf8("rbROSNavigation"));
        rbROSNavigation->setEnabled(false);
        rbROSNavigation->setMinimumSize(QSize(0, 40));
        rbROSNavigation->setChecked(false);

        horizontalLayout_8->addWidget(rbROSNavigation);

        btnROSNavigationEdit = new QPushButton(gbRobotROSNavigation);
        btnROSNavigationEdit->setObjectName(QString::fromUtf8("btnROSNavigationEdit"));
        sizePolicy1.setHeightForWidth(btnROSNavigationEdit->sizePolicy().hasHeightForWidth());
        btnROSNavigationEdit->setSizePolicy(sizePolicy1);
        btnROSNavigationEdit->setMinimumSize(QSize(94, 0));
        btnROSNavigationEdit->setStyleSheet(QString::fromUtf8("QPushButton {\n"
"color: #333;\n"
"border: 2px solid #555;\n"
"border-radius: 4px;\n"
"padding: 5px;\n"
"background: qradialgradient(cx: 0.3, cy: -0.4,\n"
"fx: 0.3, fy: -0.4,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #888);\n"
"min-width: 80px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"background: qradialgradient(cx: 0.3, cy: -0.4,\n"
"fx: 0.3, fy: -0.4,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #bbb);\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"background: qradialgradient(cx: 0.4, cy: -0.1,\n"
"fx: 0.4, fy: -0.1,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #ddd);\n"
"}"));

        horizontalLayout_8->addWidget(btnROSNavigationEdit);


        verticalLayout_9->addLayout(horizontalLayout_8);


        verticalLayout_10->addLayout(verticalLayout_9);


        verticalLayout_30->addWidget(gbRobotROSNavigation);

        gbRobotROSJnp = new QGroupBox(frame_20);
        gbRobotROSJnp->setObjectName(QString::fromUtf8("gbRobotROSJnp"));
        gbRobotROSJnp->setStyleSheet(QString::fromUtf8("QGroupBox#gbRobotROSJnp{\n"
"    border: 1px solid 	darkgray;\n"
"    margin-top: 15px;\n"
"	padding-top: 15px;\n"
"    color: white;\n"
"}\n"
"\n"
"QGroupBox#gbRobotROSJnp::title {\n"
"    subcontrol-position: top left;\n"
"    border: 1px solid white;\n"
"    background-color: gray;\n"
"    padding: 5px 15px 5px 15px;\n"
"    top: -15px;\n"
"	left: 20px;\n"
"}"));
        gbRobotROSJnp->setCheckable(false);
        gbRobotROSJnp->setChecked(false);
        verticalLayout_12 = new QVBoxLayout(gbRobotROSJnp);
        verticalLayout_12->setObjectName(QString::fromUtf8("verticalLayout_12"));
        verticalLayout_11 = new QVBoxLayout();
        verticalLayout_11->setObjectName(QString::fromUtf8("verticalLayout_11"));
        cbJnpEnable = new QCheckBox(gbRobotROSJnp);
        cbJnpEnable->setObjectName(QString::fromUtf8("cbJnpEnable"));
        cbJnpEnable->setEnabled(true);
        cbJnpEnable->setCheckable(true);
        cbJnpEnable->setChecked(true);

        verticalLayout_11->addWidget(cbJnpEnable);

        vlJnp = new QVBoxLayout();
        vlJnp->setObjectName(QString::fromUtf8("vlJnp"));
        vlJnp->setContentsMargins(20, -1, -1, -1);
        cbJnpOptionTerminal = new QCheckBox(gbRobotROSJnp);
        cbJnpOptionTerminal->setObjectName(QString::fromUtf8("cbJnpOptionTerminal"));

        vlJnp->addWidget(cbJnpOptionTerminal);


        verticalLayout_11->addLayout(vlJnp);


        verticalLayout_12->addLayout(verticalLayout_11);


        verticalLayout_30->addWidget(gbRobotROSJnp);

        verticalSpacer_3 = new QSpacerItem(20, 40, QSizePolicy::Minimum, QSizePolicy::Expanding);

        verticalLayout_30->addItem(verticalSpacer_3);


        verticalLayout_21->addWidget(frame_20);

        scrollArea_9->setWidget(scrollAreaWidgetContents_9);

        verticalLayout_19->addWidget(scrollArea_9);


        horizontalLayout_29->addWidget(gbRobotROS);


        verticalLayout->addWidget(frame_19);

        frame_4 = new QFrame(centralwidget);
        frame_4->setObjectName(QString::fromUtf8("frame_4"));
        QSizePolicy sizePolicy6(QSizePolicy::Ignored, QSizePolicy::Fixed);
        sizePolicy6.setHorizontalStretch(0);
        sizePolicy6.setVerticalStretch(25);
        sizePolicy6.setHeightForWidth(frame_4->sizePolicy().hasHeightForWidth());
        frame_4->setSizePolicy(sizePolicy6);
        frame_4->setMinimumSize(QSize(0, 40));
        frame_4->setFrameShape(QFrame::NoFrame);
        frame_4->setFrameShadow(QFrame::Plain);
        frame_4->setLineWidth(0);
        horizontalLayout_6 = new QHBoxLayout(frame_4);
        horizontalLayout_6->setSpacing(0);
        horizontalLayout_6->setObjectName(QString::fromUtf8("horizontalLayout_6"));
        horizontalLayout_6->setContentsMargins(0, 0, 0, 5);
        horizontalLayout_5 = new QHBoxLayout();
        horizontalLayout_5->setSpacing(0);
        horizontalLayout_5->setObjectName(QString::fromUtf8("horizontalLayout_5"));
        horizontalSpacer = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        horizontalLayout_5->addItem(horizontalSpacer);

        btnStartSimulator = new QPushButton(frame_4);
        btnStartSimulator->setObjectName(QString::fromUtf8("btnStartSimulator"));
        QSizePolicy sizePolicy7(QSizePolicy::Minimum, QSizePolicy::Expanding);
        sizePolicy7.setHorizontalStretch(0);
        sizePolicy7.setVerticalStretch(0);
        sizePolicy7.setHeightForWidth(btnStartSimulator->sizePolicy().hasHeightForWidth());
        btnStartSimulator->setSizePolicy(sizePolicy7);
        btnStartSimulator->setMinimumSize(QSize(100, 0));
        btnStartSimulator->setStyleSheet(QString::fromUtf8("    color: white;"));

        horizontalLayout_5->addWidget(btnStartSimulator);


        horizontalLayout_6->addLayout(horizontalLayout_5);


        verticalLayout->addWidget(frame_4);

        MainWindow->setCentralWidget(centralwidget);
        menubar = new QMenuBar(MainWindow);
        menubar->setObjectName(QString::fromUtf8("menubar"));
        menubar->setGeometry(QRect(0, 0, 1135, 22));
        menuFIle = new QMenu(menubar);
        menuFIle->setObjectName(QString::fromUtf8("menuFIle"));
        menuDB = new QMenu(menubar);
        menuDB->setObjectName(QString::fromUtf8("menuDB"));
        MainWindow->setMenuBar(menubar);
        statusbar = new QStatusBar(MainWindow);
        statusbar->setObjectName(QString::fromUtf8("statusbar"));
        MainWindow->setStatusBar(statusbar);
        QWidget::setTabOrder(scrollArea, btnStartSimulator);

        menubar->addAction(menuFIle->menuAction());
        menubar->addAction(menuDB->menuAction());
        menuFIle->addAction(actionOpen);
        menuFIle->addAction(actionSave);
        menuFIle->addAction(actionSave_as);
        menuFIle->addSeparator();
        menuFIle->addAction(actionExit);
        menuDB->addAction(actionOpenDB);

        retranslateUi(MainWindow);

        QMetaObject::connectSlotsByName(MainWindow);
    } // setupUi

    void retranslateUi(QMainWindow *MainWindow)
    {
        MainWindow->setWindowTitle(QCoreApplication::translate("MainWindow", "3DAgent Simulator", nullptr));
        actionSave->setText(QCoreApplication::translate("MainWindow", "Save", nullptr));
        actionSave_as->setText(QCoreApplication::translate("MainWindow", "Save as", nullptr));
        actionExis->setText(QCoreApplication::translate("MainWindow", "Exit", nullptr));
        actionExit->setText(QCoreApplication::translate("MainWindow", "Exit", nullptr));
        actionOpen->setText(QCoreApplication::translate("MainWindow", "Open", nullptr));
        actionOpenDB->setText(QCoreApplication::translate("MainWindow", "Open", nullptr));
        gbWorld->setTitle(QCoreApplication::translate("MainWindow", "World", nullptr));
        lbWorldImage->setText(QString());
        groupBox_5->setTitle(QCoreApplication::translate("MainWindow", "Option", nullptr));
        chkWorldOptionPerson->setText(QString());
        label->setText(QCoreApplication::translate("MainWindow", "Person", nullptr));
        lbRandomColor->setText(QCoreApplication::translate("MainWindow", "Random Color", nullptr));
        chkWorldOptionRandomColor->setText(QString());
        label_3->setText(QCoreApplication::translate("MainWindow", "Bulding", nullptr));
        label_2->setText(QCoreApplication::translate("MainWindow", "Random Color", nullptr));
        checkBox->setText(QString());
        gbRobot->setTitle(QCoreApplication::translate("MainWindow", "Robot", nullptr));
        btnAddRobot->setText(QCoreApplication::translate("MainWindow", "Add", nullptr));
        btnDeleteRobot->setText(QCoreApplication::translate("MainWindow", "Delete", nullptr));
        btnAddModel->setText(QCoreApplication::translate("MainWindow", "Add model", nullptr));
        gbRobotROS->setTitle(QCoreApplication::translate("MainWindow", "ROS", nullptr));
        gbRobotROSControl->setTitle(QCoreApplication::translate("MainWindow", "Control", nullptr));
        btnROSTeleop->setText(QCoreApplication::translate("MainWindow", "Teleop", nullptr));
        gbRobotROSNavigation->setTitle(QCoreApplication::translate("MainWindow", "Navigation", nullptr));
        rbROSNone->setText(QCoreApplication::translate("MainWindow", "None", nullptr));
        rbROSSlam->setText(QCoreApplication::translate("MainWindow", "Slam", nullptr));
        btnROSSlamEdit->setText(QCoreApplication::translate("MainWindow", "edit", nullptr));
        rbROSNavigation->setText(QCoreApplication::translate("MainWindow", "Navigation", nullptr));
        btnROSNavigationEdit->setText(QCoreApplication::translate("MainWindow", "edit", nullptr));
        gbRobotROSJnp->setTitle(QCoreApplication::translate("MainWindow", "Jnp", nullptr));
        cbJnpEnable->setText(QCoreApplication::translate("MainWindow", "Enable", nullptr));
        cbJnpOptionTerminal->setText(QCoreApplication::translate("MainWindow", "Run the script in terminal", nullptr));
        btnStartSimulator->setText(QCoreApplication::translate("MainWindow", "Start", nullptr));
        menuFIle->setTitle(QCoreApplication::translate("MainWindow", "File", nullptr));
        menuDB->setTitle(QCoreApplication::translate("MainWindow", "DB", nullptr));
    } // retranslateUi

};

namespace Ui {
    class MainWindow: public Ui_MainWindow {};
} // namespace Ui

QT_END_NAMESPACE

#endif // MAINTCSTUK_H
