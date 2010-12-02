/***************************************************************************
 *
 * Authors:     Carlos Oscar S. Sorzano (coss@cnb.csic.es)
 *              Carlos Manzanares       (cmanzana@cnb.csic.es)
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

#include <data/args.h>

#include <qapplication.h>

#include "main_widget_mark.h"
#include "widget_psd.h"
#include "widget_micrograph.h"

class ProgMicrographMark: public XmippProgram
{
private:

protected:
    void defineParams()
    {

        addUsageLine ("Mark particles in a micrograph\n");

        addParamsLine("  -i <input_untilted_micrograph>      : File with untilted image");
        addParamsLine("     alias --untilted;");
        addParamsLine("  [-t <input_tilted_micrograph>]      : File with tilted image");
        addParamsLine("     alias --tilted;");
        addParamsLine("  [--psd <assign_CTF_prm_file>]       : Show the PSDs\n");
        addParamsLine("  [--ctf <assign_CTF_prm_file>]       : Show the CTF models\n");
        addParamsLine("  [--auto <model_rootname>]           : For autoselection\n");
        addParamsLine("  [--autoSelect]                          : Autoselect without user interaction\n");
        addParamsLine("  [--thr <p=1>]                           : Number of threads for automatic picking\n");
    }
    FileName fnRaw;
    FileName fnRawTilted;
    FileName fnAutomaticModel;
    //bool     reversed;
    FileName fn_assign_CTF;
    bool     ctf_mode;
    bool     autoSelect;
    int      numThreads;

    void readParams()
    {
        ctf_mode   = false;
        autoSelect = false;
        // Get input parameters .................................................
        fnRaw         = getParam( "-i");
        if(checkParam("--tilted"))
            fnRawTilted   = getParam("--tilted");
        else
            fnRawTilted   ="";
        if(checkParam("--psd"))
            fn_assign_CTF = getParam("--psd");
        else
            fn_assign_CTF="";
        if (checkParam("--ctf"))
        {
            ctf_mode = true;
            fn_assign_CTF = getParam("--ctf");
        }
        if(checkParam("--auto"))
            fnAutomaticModel = getParam("--auto");
        else
            fnAutomaticModel ="";
        autoSelect = checkParam("--autoSelect");
        if (fnRawTilted!="" && autoSelect)
            REPORT_ERROR(ERR_VALUE_INCORRECT,"Automatic particle picking cannot be performed on tilt pairs");
        numThreads = getIntParam("--thr");
    }
public:
    void run()
    {
        Micrograph m, mTilted;
        FileName fn8bits="", fn8bitsTilted="";

        m.open_micrograph(fnRaw);
        std::vector<FileName> filesToDelete;
        fn8bits=fnRaw+"_8bits.raw";
        m.write(fn8bits+"%uint8",true);
        m.close_micrograph();

        m.open_micrograph(fn8bits);
        m.resetLinearTransformatioVal8();
        m.set_micrograph_name(fnRaw);
        filesToDelete.push_back(fn8bits+"*");

        if (fnRawTilted != "")
        {
            mTilted.open_micrograph(fnRawTilted);
            fn8bitsTilted=fnRawTilted+"_8bits.raw";
            mTilted.write(fn8bitsTilted+"%uint8");
            mTilted.close_micrograph();
            mTilted.open_micrograph(fn8bitsTilted);
            mTilted.set_micrograph_name(fnRawTilted);
            mTilted.resetLinearTransformatioVal8();
            filesToDelete.push_back(fn8bitsTilted+"*");
        }

        // Configure application .............................................
        AutoParticlePicking *autoPicking=NULL;
        autoPicking=new AutoParticlePicking(&m);

        QApplication *app=NULL;
        QtMainWidgetMark *mainWidget=NULL;
        if (!autoSelect)
        {
            app=new QApplication(argc, argv);
            if (fnRawTilted == "")
            {
                mainWidget = new QtMainWidgetMark(&m);
                mainWidget->untilted_widget()->
                setAutoParticlePicking(autoPicking);
            }
            else
                mainWidget = new QtMainWidgetMark(&m, &mTilted);
            for (int i=0; i<filesToDelete.size(); i++)
                mainWidget->__filesToDelete.push_back(filesToDelete[i]);
        }

        // Check if the PSDs must be shown ...................................
        if (fn_assign_CTF != "")
        {
            QtWidgetPSD PSDshow;
            if (ctf_mode)
                PSDshow.set_CTF_mode();
            PSDshow.set_assign_CTF_file(m, fn_assign_CTF);
            PSDshow.show();
        }

        // Check if a model has been provided ................................
        autoPicking->setNumThreads(numThreads);
        if (fnAutomaticModel!="")
            autoPicking->loadModels(fnAutomaticModel);

        // Run application ...................................................
        if (!autoSelect)
        {
            app->setMainWidget(mainWidget);
            mainWidget->openAllWindows();
            app->exec();
        }
        else
        {
            autoPicking->automaticallySelectParticles();
            autoPicking->saveAutoParticles();
        }
    }
};

int main(int argc, char **argv)
{
    try
    {
        ProgMicrographMark program;
        program.read(argc, argv);
        program.run();
    }
    catch (XmippError e)
    {
        std::cerr << e.msg <<std::endl;
    }
    return 0;
}
