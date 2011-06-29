#ifndef XMIPP_INTERNAL_DATA
#define XMIPP_INTERNAL_DATA
#include <jni.h>
#include <data/xmipp_image.h>
#include <data/xmipp_image_generic.h>
#include <data/projection.h>
#include <data/ctf.h>

static jfieldID ImageDouble_peerId;
static jfieldID ImageGeneric_peerId;
static jfieldID Projection_peerId;
static jfieldID MetaData_peerId;
static jfieldID CTFDescription_peerId;

#define peerId ImageDouble_peerId
#define peerId ImageGeneric_peerId
#define peerId Projection_peerId
#define peerId MetaData_peerId
#define peerId CTFDescription_peerId

#define GET_INTERNAL_IMAGE(obj) ((Image<double> *)(env->GetLongField(obj, peerId)))
#define GET_INTERNAL_IMAGE_GENERIC(obj) ((ImageGeneric *)(env->GetLongField(obj, peerId)))
#define GET_INTERNAL_PROJECTION(obj) ((Projection *)(env->GetLongField(obj, peerId)))
#define GET_INTERNAL_METADATA(obj) ((MetaData *)(env->GetLongField(obj, peerId)))
#define GET_INTERNAL_CTFDESCRIPTION(obj) ((CTFDescription *)(env->GetLongField(obj, peerId)))

#endif
