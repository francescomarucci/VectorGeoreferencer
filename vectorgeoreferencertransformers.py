# -*- coding: utf-8 -*-
from qgis.core import *
import math
from decimal import *

class Transformer():
    """
    Represents an abstract transfromation type
    """
    def __init__(self, pairsLayer ):
        
        self.pointsA = []
        self.pointsB = []
        features = pairsLayer.getFeatures()

        for feature in features:
            geom = feature.geometry().asPolyline()
            self.pointsA.append( QgsPoint(geom[0].x(),geom[0].y()) )
            self.pointsB.append( QgsPoint(geom[-1].x(),geom[-1].y()) )


    def map(self, p):
        return p


class AffineTransformer(Transformer):
    def __init__(self, pairsLayer ):
        Transformer.__init__(self, pairsLayer )      

        # Make sure data is valid
        assert len(self.pointsA)>=3
        assert len(self.pointsA)==len(self.pointsB)
        
        self.affineParams=self.calculateAffineParams(self.pointsA,self.pointsB)
        
    def map(self, p):
      
        a=self.affineParams[0]
        b=self.affineParams[1]
        c=self.affineParams[2]
        d=self.affineParams[3]
        tx=self.affineParams[4]
        ty=self.affineParams[5]
        
        return QgsPoint(a*Decimal(p[0])+b*Decimal(p[1])+tx, c*Decimal(p[0])+d*Decimal(p[1])+ty)

    def calculateAffineParams(self, p1, p2 ):
        getcontext().prec = 22
        
        cc00=len(p1)
    
        cc01=Decimal(0)
        cc02=Decimal(0)
        cc11=Decimal(0)
        cc12=Decimal(0)
        cc22=Decimal(0)
        aa0=Decimal(0)
        aa1=Decimal(0)
        aa2=Decimal(0)
        bb0=Decimal(0)
        bb1=Decimal(0)
        bb2=Decimal(0)        
        
        for i in range(cc00):
          
          to_x=Decimal(p1[i].x())
          to_y=Decimal(p1[i].y())
          from_x=Decimal(p2[i].x())
          from_y=Decimal(p2[i].y())
            
          cc01+=to_x
          cc02+=to_y
          cc11+=to_x**2
          cc12+=to_x*to_y
          cc22+=to_y**2
          aa0+=from_y
          aa1+=from_y*to_x
          aa2+=from_y*to_y
          bb0+=from_x
          bb1+=from_x*to_x
          bb2+=from_x*to_y

        cc_det= (cc00*cc11*cc22)+(cc01*cc12*cc02)+(cc02*cc01*cc12)-(cc00*cc12*cc12)-(cc01*cc01*cc22)-(cc02*cc11*cc02)
        inv_cc00=(cc11*cc22-cc12*cc12)/cc_det
        inv_cc01=(cc12*cc02-cc01*cc22)/cc_det
        inv_cc02=(cc01*cc12-cc11*cc02)/cc_det
        inv_cc11=(cc00*cc22-cc02*cc02)/cc_det
        inv_cc12=(cc01*cc02-cc00*cc12)/cc_det
        inv_cc22=(cc00*cc11-cc01*cc01)/cc_det

        a=(bb0*inv_cc01+bb1*inv_cc11+bb2*inv_cc12)
        b=(bb0*inv_cc02+bb1*inv_cc12+bb2*inv_cc22)
        c=(aa0*inv_cc01+aa1*inv_cc11+aa2*inv_cc12)
        d=(aa0*inv_cc02+aa1*inv_cc12+aa2*inv_cc22)
        tx=(bb0*inv_cc00+bb1*inv_cc01+bb2*inv_cc02)
        ty=(aa0*inv_cc00+aa1*inv_cc01+aa2*inv_cc02)
        
        #QgsMessageLog.logMessage("a: "+str(a)+", b: "+str(b)+", c: "+str(c)+", d: "+str(d)+", tx: "+str(tx)+", ty:"+str(ty), 'AffineTransformer Parameters')

        return (a,b,c,d,tx,ty)
      
      
class LinearTransformer(Transformer):
    def __init__(self, pairsLayer ):
        Transformer.__init__(self, pairsLayer )

        # Make sure data is valid
        assert len(self.pointsA)==2
        assert len(self.pointsA)==len(self.pointsB)

        self.a1 = self.pointsA[0]
        self.a2 = self.pointsA[1]
        self.b1 = self.pointsB[0]
        self.b2 = self.pointsB[1]

        #scale 
        self.ds = math.sqrt( (self.b2.x()-self.b1.x())**2.0+(self.b2.y()-self.b1.y())**2.0 ) / math.sqrt( (self.a2.x()-self.a1.x())**2.0+(self.a2.y()-self.a1.y())**2.0 )
        #rotation
        self.da =  math.atan2( self.b2.y()-self.b1.y(), self.b2.x()-self.b1.x() ) - math.atan2( self.a2.y()-self.a1.y(), self.a2.x()-self.a1.x() )
        #translation
        self.dx1 = self.pointsA[0].x()
        self.dy1 = self.pointsA[0].y() 
        self.dx2 = self.pointsB[0].x()
        self.dy2 = self.pointsB[0].y()


    def map(self, p):

        #move to origin (translation part 1)
        p = QgsPoint( p.x()-self.dx1, p.y()-self.dy1 )

        #scale 
        p = QgsPoint( self.ds*p.x(), self.ds*p.y() )

        #rotation
        p = QgsPoint( math.cos(self.da)*p.x() - math.sin(self.da)*p.y(), math.sin(self.da)*p.x() + math.cos(self.da)*p.y() )

        #remove to right spot (translation part 2)
        p = QgsPoint( p.x()+self.dx2, p.y()+self.dy2 )

        return p

class TranslationTransformer(Transformer):
    def __init__(self, pairsLayer ):
        Transformer.__init__(self, pairsLayer )

        # Make sure data is valid
        assert len(self.pointsA)==1 
        assert len(self.pointsA)==len(self.pointsB)

        self.dx = self.pointsB[0].x()-self.pointsA[0].x()
        self.dy = self.pointsB[0].y()-self.pointsA[0].y()

    def map(self, p):
        return QgsPoint(p[0]+self.dx, p[1]+self.dy)

