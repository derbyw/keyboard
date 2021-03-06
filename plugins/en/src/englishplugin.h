﻿#ifndef ENGLISHPLUGIN_H
#define ENGLISHPLUGIN_H

#include <QObject>
#include "westernlanguagesplugin.h"

//#include <presage.h>

class EnglishPlugin : public WesternLanguagesPlugin
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID "org.qt-project.Qt.Examples.EnglishPlugin" FILE "englishplugin.json")

public:
    explicit EnglishPlugin(QObject* parent = nullptr)
        : WesternLanguagesPlugin(parent)
    {
    }

    ~EnglishPlugin() override = default;
};

#endif // ENGLISHPLUGIN_H
