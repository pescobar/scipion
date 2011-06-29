/***************************************************************************
 *
 * Authors:      Alberto Pascual Montano (pascual@cnb.csic.es)
 *               Carlos Oscar S. Sorzano (coss@cnb.csic.es)
 *
 * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
 * 02111-1307  USA
 *
 *  All comments concerning this program package may be sent to the
 *  e-mail address 'xmipp@cnb.csic.es'
 ***************************************************************************/

#include "show_tools.h"


#include <qfile.h>
#include <qlayout.h>
#include <qmime.h>
#include <qpushbutton.h>
#include <qtooltip.h>
#ifdef QT3_SUPPORT
#include <q3dragobject.h>
//Added by qt3to4:
#include <Q3GridLayout>
#include <QPixmap>
#include <QLabel>
#include <Q3VBoxLayout>
#else
#include <qdragobject.h>
#endif

#include <data/xmipp_fft.h>
#include <data/histogram.h>
#include <data/args.h>

ScrollParam::ScrollParam(float min , float max, float initial_value,
                         char* prm_name, char *caption, QWidget *parent, const char *name,
                         int wFlags, int precision) :
#ifdef QT3_SUPPORT
        QWidget(parent, name, (Qt::WindowFlags) wFlags)
#else
        QWidget(parent, name, wFlags)
#endif
{
    std::vector<float> vmin;
    vmin.push_back(min);
    std::vector<float> vmax;
    vmax.push_back(max);
    std::vector<float> vinitial_value;
    vinitial_value.push_back(initial_value);
    std::vector<char *> vprm_name;
    vprm_name.push_back(prm_name);
    init(vmin, vmax, vinitial_value, vprm_name, caption, precision);
}

ScrollParam::ScrollParam(std::vector<float> &min , std::vector<float> &max,
                         std::vector<float> &initial_value, std::vector<char *> &prm_name,
                         char *caption, QWidget *parent, const char *name, int wFlags, int precision) :
#ifdef QT3_SUPPORT
        QWidget(parent, name, (Qt::WindowFlags) wFlags)
#else
        QWidget(parent, name, wFlags)
#endif
{
    init(min, max, initial_value, prm_name, caption, precision);
}

void ScrollParam::init(std::vector<float> &min, std::vector<float> &max,
                       std::vector<float> &initial_value, std::vector<char *> &prm_name,
                       char *caption, int precision)
{

    // Set the selfWindow caption/title
    setCaption(caption);

    // Set precision
    my_precision = (int)pow((double)10, (double)precision);

    // Create a layout to position the widgets
#ifdef QT3_SUPPORT
    Q3BoxLayout *Layout = new Q3VBoxLayout(this, 10);
    Q3GridLayout *grid = new Q3GridLayout(3 + min.size(), 5);
#else
    QBoxLayout *Layout = new QVBoxLayout(this, 10);
    QGridLayout *grid = new QGridLayout(3 + min.size(), 5);
#endif
    Layout->addLayout(grid, 5);

    // Title
    QLabel *title = new QLabel(this, "title");
    title->setFont(QFont("times", 14, QFont::Bold));
    title->setText(caption);
    title->setFixedSize(title->sizeHint());
    grid->addMultiCellWidget(title, 0, 0, 0, 2);

    // Add all parameters
    value = initial_value;
    for (int i = 0; i < min.size(); i++)
    {
        int tmp_min = (int)(min[i] * my_precision);
        int tmp_max = (int)(max[i] * my_precision);
        value[i]    = (float) initial_value[i] * my_precision;

        // Add Parameter name
        QLabel     *lab1 = new QLabel(this, "lab1");
        lab1->setFont(QFont("times", 12, QFont::Bold));
        lab1->setText(prm_name[i]);
        lab1->setFixedSize(lab1->sizeHint());
        grid->addWidget(lab1, i + 1, 0, Qt::AlignLeft);

        // Add range
        QLabel     *lab2 = new QLabel(this, "lab2");
        lab2->setFont(QFont("times", 12));
        lab2->setText(((std::string)"[" + floatToString(min[i], 0) + "," + floatToString(max[i], 0) + "]").c_str());
        lab2->setFixedSize(lab2->sizeHint());
        grid->addWidget(lab2, i + 1, 1, Qt::AlignCenter);

        // Add Scroll Bar
        QScrollBar  *scroll_aux = new QScrollBar(tmp_min, tmp_max, 1, 1, (int)value[i], Qt::Horizontal, this, "scroll");
        scroll_aux->setFixedWidth(100);
        scroll_aux->setFixedHeight(15);
        grid->addMultiCellWidget(scroll_aux, i + 1, i + 1, 2, 3);
        scroll.push_back(scroll_aux);

        // Label for the current value
        QLabel * value_lab_aux;
        value_lab_aux = new QLabel(this, "value_lab");
        value_lab_aux->setFont(QFont("times", 12));
        value_lab_aux->setNum(value[i] / my_precision);
        grid->addWidget(value_lab_aux, i + 1, 4, Qt::AlignLeft);
        value_lab.push_back(value_lab_aux);

        connect(scroll_aux, SIGNAL(valueChanged(int)), SLOT(scrollValueChanged(int)));
    }

    // Close Button
    QPushButton *close;
    close = new QPushButton(this, "close");     // create button 1
    close->setFont(QFont("times", 12, QFont::Bold));
    close->setText("Close");
    close->setFixedSize(close->sizeHint());
    grid->addWidget(close, 1 + min.size(), 0, Qt::AlignVCenter);
    QToolTip::add(close, "Close the window");
    connect(close, SIGNAL(clicked()), SLOT(slot_close_clicked()));

    // OK button
    QPushButton *do_it;
    do_it = new QPushButton(this, "do_it");     // create button 3
    do_it->setFont(QFont("times", 12, QFont::Bold));
    do_it->setText("Ok");
    do_it->setFixedHeight(do_it->sizeHint().height());
    do_it->setFixedWidth(80);
    grid->addWidget(do_it, 1 + min.size(), 3, Qt::AlignVCenter);
    QToolTip::add(do_it, "Commit action");
    connect(do_it, SIGNAL(clicked()), SLOT(slot_ok_clicked()));
}

ScrollParam::~ScrollParam()
{
    for (int i = 0; i < value.size(); i++)
    {
        delete value_lab[i];
        delete scroll[i];
    }
}

std::vector<float> ScrollParam::getCurrentValues()
{
    for (int i = 0; i < value.size(); i++)
    {
        int v = scroll[i]->value();
        value[i] = (float)v / my_precision;
        value_lab[i]->setNum(value[i]);
    }
    return value;
}

void ScrollParam::scrollValueChanged(int v)
{
    getCurrentValues();
    emit new_value(value[0]);
    emit new_value(value);
}

void ScrollParam::slot_close_clicked()
{
    emit signal_close_clicked();
    close();
}

void ScrollParam::slot_ok_clicked()
{
    emit new_value(value[0]);
    emit new_value(value);
    emit signal_ok_clicked();
    close();
}


ExclusiveParam::ExclusiveParam(std::vector<std::string> &list_values, int initial_value,
                               char *caption, QWidget *parent, const char *name, int wFlags) :
#ifdef QT3_SUPPORT
        QWidget(parent, name, (Qt::WindowFlags) wFlags)
#else
        QWidget(parent, name, wFlags)
#endif
{
    float my_precision = 0;
    int tmp_min = (int) 0;
    int tmp_max = (int) 1;
    value  = (int)initial_value;
    QColor col;
    // Set the selfWindow caption/title

    setCaption(caption);

    // Create a layout to position the widgets
#ifdef QT3_SUPPORT
    Q3BoxLayout *Layout = new Q3VBoxLayout(this, 10);
#else
    QBoxLayout* Layout = new QVBoxLayout(this, 10);
#endif

    // Create a grid layout to hold most of the widgets
#ifdef QT3_SUPPORT
    Q3GridLayout *grid = new Q3GridLayout(5 + list_values.size(), 3);
#else
    QGridLayout* grid = new QGridLayout(5 + list_values.size(), 3);
#endif

    // This layout will get all of the stretch
    Layout->addLayout(grid, 5);

    //title
    QLabel     *title = new QLabel(this, "title");
    title->setFont(QFont("times", 14, QFont::Bold));
    title->setText("FFT show mode");
    title->setFixedSize(title->sizeHint());
    grid->addMultiCellWidget(title, 0, 0, 0, 2);

    // Set all QRadioButtons
    for (int i = 0; i < list_values.size(); i++)
    {
        button.push_back(new QRadioButton(list_values[i].c_str(), this, "radiobutton"));
        if (i == initial_value) button[i]->setChecked(true);
        connect(button[i], SIGNAL(toggled(bool)), this, SLOT(exclusiveValueChanged()));
        grid->addMultiCellWidget(button[i], 2 + i, 2 + i, 0, 2);
    }

    //Close Button
    QPushButton *close;
    close = new QPushButton(this, "close");     // create button 1
    close->setFont(QFont("times", 12, QFont::Bold));
    close->setText("Close");
    close->setFixedSize(close->sizeHint());
    grid->addWidget(close, 3 + list_values.size(), 0, Qt::AlignVCenter);
    QToolTip::add(close, "Close the window");
    connect(close, SIGNAL(clicked()), SLOT(but_close_clicked()));

    QPushButton *do_it;
    do_it = new QPushButton(this, "do_it");     // create button 3
    do_it->setFont(QFont("times", 12, QFont::Bold));
    do_it->setText("Ok");
    do_it->setFixedHeight(do_it->sizeHint().height());
    do_it->setFixedWidth(80);
    grid->addWidget(do_it, 3 + list_values.size(), 2, Qt::AlignVCenter);
    QToolTip::add(do_it, "Commit action");
    connect(do_it, SIGNAL(clicked()), SLOT(but_ok_clicked()));
}

ExclusiveParam::~ExclusiveParam()
{}

void ExclusiveParam::but_close_clicked()
{
    close();
}

void ExclusiveParam::but_ok_clicked()
{
    emit new_value(value);
    close();
}

void ExclusiveParam::exclusiveValueChanged()
{
    // Count the number of active buttons
    int N = 0;
    for (int i = 0; i < button.size(); i++)
        if (button[i]->isChecked()) N++;
    if (N == 0) button[value]->setChecked(true);
    else if (N > 1)
    {
        button[value]->setChecked(false);
        for (int i = 0; i < button.size(); i++)
            if (button[i]->isChecked())
            {
                value = i;
                break;
            }
    }
}

/* Qimage -> Xmipp --------------------------------------------------------- */
void Qt2xmipp(QImage &_qimage, Image<double> &_ximage)
{
    _ximage().resize(_qimage.height(), _qimage.width());
    for (int y = 0; y < _qimage.width(); y++)
        for (int x = 0; x < _qimage.height(); x++)
            _ximage()(x, y) = (double) _qimage.pixelIndex(y, x);
}

/* Xmipp -> QImage --------------------------------------------------------- */
void xmipp2Qt(Image<double>& _ximage, QImage &_qimage, int _min_scale,
              int _max_scale, double _m, double _M)
{
    // Creates a Qt Image to hold Xmipp Image
    _qimage.create(XSIZE(_ximage()), YSIZE(_ximage()), 8, 256);

    // Sets Graylevel Palette.
    for (int i = 0; i < 256; i++)
    {
        QColor c;
        c.setRgb(i, i, i);
        _qimage.setColor(i, c.rgb());
    }

    const MultidimArray<double> &xmatrix = _ximage();
    int xdim = XSIZE(xmatrix);
    int ydim = YSIZE(xmatrix);
    double min_val, max_val;
    if (_m == 0 && _M == 0) xmatrix.computeDoubleMinMax(min_val, max_val);
    else
    {
        min_val = _m;
        max_val = _M;
    }
    double a;
    if (_max_scale - _min_scale < XMIPP_EQUAL_ACCURACY ||
    // Sjors 17may07: prevent division by zero for constant images
        max_val - min_val < XMIPP_EQUAL_ACCURACY)
        a = 1.0;
    else
        a = (_max_scale - _min_scale) / (max_val - min_val);

    // Reads pixels.
    for (int y = 0; y < ydim; y++)
        for (int x = 0; x < xdim; x++)
            _qimage.setPixel(x, y, ((uint) CLIP((a*(
                                                     DIRECT_A2D_ELEM(xmatrix, y, x) - min_val) + _min_scale), 0, 255)));
}

/* Xmipp -> Pixmap --------------------------------------------------------- */
void xmipp2Pixmap(Image<double> &xmippImage, QPixmap* pixmap,
                  int _minScale, int _maxScale, double _m, double _M)
{
    QImage tmpImage;
    xmipp2Qt(xmippImage, tmpImage, _minScale, _maxScale, _m, _M);
    pixmap->convertFromImage(tmpImage, 0);
}

/* Pixmap from MIME source ------------------------------------------------- */
QPixmap xmipp_qPixmapFromMimeSource(const QString &abs_name)
{
#ifdef QT3_SUPPORT
    const QMimeSource *m = Q3MimeSourceFactory::defaultFactory()->data(abs_name);
#else
    const QMimeSource *m = QMimeSourceFactory::defaultFactory()->data(abs_name);
#endif
    if (!m)
    {
        if (QFile::exists(abs_name))
            return QPixmap(abs_name);
        return QPixmap();
    }
    QPixmap pix;
#ifdef QT3_SUPPORT
    Q3ImageDrag::decode(m, pix);
#else
    QImageDrag::decode(m, pix);
#endif
    return pix;
}
