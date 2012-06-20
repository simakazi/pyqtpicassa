#!/usr/bin/python
# -*- coding: utf8 -*-
import gdata.photos.service
import gdata.media
import gdata.geo
from PyQt4 import Qt,QtCore,QtGui, QtNetwork
import sys
import urllib2
from PyQt4.QtWebKit import QWebPage


app = QtGui.QApplication(sys.argv)


net_man=QtNetwork.QNetworkAccessManager()

class Slide(QtGui.QLabel):
    deleteMe=QtCore.pyqtSignal(QtGui.QWidget)
    def __init__(self,photo_data,parent=None):
        QtGui.QLabel.__init__(self,parent)
        self.photo=photo_data
        request = QtNetwork.QNetworkRequest()            
        request.setUrl(QtCore.QUrl(self.photo.media.thumbnail[1].url));            
        self.reply=net_man.get(request)        
        self.reply.finished.connect(self.load_image)
        act_del=QtGui.QAction("Delete",self)
        self.addAction(act_del)
        act_del.triggered.connect(self.__del_clicked__)        
        act_link=QtGui.QAction("Copy link",self)
        self.addAction(act_link)
        act_link.triggered.connect(self.__copy_link__)
        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        
    def __del_clicked__(self):
        self.deleteMe.emit(self)
        
    def __copy_link__(self):
        app.clipboard().setText('<table style="width:auto;"><tr><td><a href="%s"><img src="%s" height="100px" /></a></td></tr></table>' % (self.photo.content.src, self.photo.media.thumbnail[1].url))
        
    @QtCore.pyqtSlot()
    def load_image(self):        
        image=QtGui.QImage()
        image.load(self.reply,'jpg')
        self.setPixmap(QtGui.QPixmap.fromImage(image))

class UploadImageThread(QtCore.QThread):
    uploadProcess = QtCore.pyqtSignal(int, int)
    def __init__(self,album_url,filename,parent=None):
        QtCore.QThread.__init__(self,parent)
        self.album_url=album_url
        self.filename=filename              
        
    def run(self):        
        L=filter(lambda x:x!="",self.filename.split('\n'))
        self.uploadProcess.emit(0,len(L))
        for x in xrange(len(L)):
            name=L[x]
            if name!='':
                name=name.replace('file://','')
                f=''
                try:
                    f=file(name,"rb")                
                    photo = gd_client.InsertPhotoSimple(self.album_url, name, '', f, content_type='image/jpeg')
                except:
                    continue                
                self.uploadProcess.emit(x+1,len(L))
        self.uploadProcess.emit(len(L),len(L))
                
        
                
        
class MainWindow(QtGui.QWidget):
    def __init__(self,gd_client,parent=None):   
        QtGui.QWidget.__init__(self,parent)
        vl = QtGui.QVBoxLayout(self)
        
        
        hl = QtGui.QHBoxLayout()        
        self.combo = QtGui.QComboBox(self)
        self.newAlbum = QtGui.QPushButton(self)
        self.newAlbum.setText('New album')
        hl.addWidget(self.combo)
        hl.addWidget(self.newAlbum)
        self.newAlbum.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
        
        vl.addLayout(hl)
        self.w = QtGui.QWidget(self)
        self.grid = QtGui.QHBoxLayout(self.w)
        self.grid.setSizeConstraint(QtGui.QLayout.SetMinAndMaxSize)
        self.slider = QtGui.QScrollArea(self)
        self.slider.setWidget(self.w)        
        vl.addWidget(self.slider)
        self.gd_client = gd_client        
        self.__load_albums__()        
        self.__load_photos__()
        self.w.setMinimumSize(QtCore.QSize(100,100))
        self.w.setMaximumSize(QtCore.QSize(100,100))        
        self.setAcceptDrops(True)
        self.status = QtGui.QLabel(self)
        self.setMinimumSize(QtCore.QSize(300,300))
        vl.addWidget(self.status)
        
        self.combo.currentIndexChanged.connect(self.__load_photos__)
        self.newAlbum.clicked.connect(self.__create_album__)
        
    def __create_album__(self):        
        name = QtGui.QInputDialog.getText(self, "Please, enter new album name","Album name", QtGui.QLineEdit.Normal,"New album")
        if name[1] and name[0]!="":            
            album = self.gd_client.InsertAlbum(title=str(name[0]),summary='')
            self.combo.insertItem(0,self.tr(album.title.text)+"("+self.tr(album.numphotos.text)+")",album.gphoto_id.text)        
            self.combo.setCurrentIndex(0)
           
            #while self.combo.count():
            #    self.combo.removeItem(0)
            #self.__load_albums__()
            
    
    def add_photo(self,photo):               
        slide=Slide(photo)       
        self.connect(slide,QtCore.SIGNAL('deleteMe(QWidget*)'),self,QtCore.SLOT('deleteSlide(QWidget*)'))
        self.grid.addWidget(slide)
        self.w.setMinimumSize(QtCore.QSize(self.grid.count()*100,100))
        self.w.setMaximumSize(QtCore.QSize(self.grid.count()*100,100))
        
    def __load_photos__(self):
        photos = self.gd_client.GetFeed('/data/feed/api/user/%s/albumid/%s?kind=photo' % ( self.gd_client.email, self.combo.itemData(self.combo.currentIndex()).toString()))
        
        self.__clear_grid__()
        for photo in photos.entry:            
            self.add_photo(photo)
    
    def __clear_grid__(self):        
        L=self.grid.count()        
        for i in xrange(L):      
            self.grid.itemAt(0).widget().hide()        
            self.grid.removeItem(self.grid.itemAt(0))        
        self.w.setMinimumSize(QtCore.QSize(100,100))
        self.w.setMaximumSize(QtCore.QSize(100,100))       
    
    def __load_albums__(self):
        albums = self.gd_client.GetUserFeed(user=gd_client.email)
        for album in albums.entry:
            #print album.title.text
            self.combo.addItem(self.tr(album.title.text)+"("+self.tr(album.numphotos.text)+")",album.gphoto_id.text)        
            
    @QtCore.pyqtSlot(QtGui.QWidget)
    def deleteSlide(self,slide):
        self.gd_client.Delete(slide.photo)
        slide.hide()        
        self.grid.removeWidget(slide)   
        self.combo.setItemText(self.combo.currentIndex(),self.combo.currentText().left(self.combo.currentText().lastIndexOf("("))+"("+str(self.grid.count())+")")
        
    @QtCore.pyqtSlot(int,int)
    def updateUploadProcess(self,done,total):
        self.status.setText("Uploading... Done "+str(done)+ " of "+str(total)+".")        
        if done==total:            
            self.combo.setEnabled(True)
            self.w.setEnabled(True)
            self.__load_photos__()
            self.status.setText("")
            self.combo.setItemText(self.combo.currentIndex(),self.combo.currentText().left(self.combo.currentText().lastIndexOf("("))+"("+str(self.grid.count())+")")
    
    def mousePressEvent(self,event):
        if event.button() == QtCore.Qt.LeftButton:
            slide=self.childAt(event.pos())
            if isinstance(slide,Slide):
                drag = QtGui.QDrag(self)
                mimeData = QtCore.QMimeData()
                #mimeData.setText(slide.photo.content.src);
                mimeData.setUrls([QtCore.QUrl(slide.photo.content.src)]);
                """
                f=urllib2.urlopen(slide.photo.content.src)
                content=f.read()
                f.close()
                
                array=QtCore.QByteArray(content)
                image=QtGui.QImage()
                image.loadFromData(array)
                pixmap=QtGui.QPixmap.fromImage(image)
                mimeData.setImageData(pixmap)                        
                """
                drag.setMimeData(mimeData);
                drag.setPixmap(slide.pixmap())
                dropAction = drag.exec_()        
    
    def dragEnterEvent(self,event):        
        if event.mimeData().hasFormat("text/plain"):
            event.acceptProposedAction()
            
    def dropEvent(self,event):
        album_url = '/data/feed/api/user/%s/albumid/%s' % ( self.gd_client.email, self.combo.itemData(self.combo.currentIndex()).toString())
        filename=str(event.mimeData().text())
        self.combo.setEnabled(False)
        self.w.setEnabled(False)            
        upload_thread=UploadImageThread(album_url,filename,self)
        self.connect(upload_thread,QtCore.SIGNAL('uploadProcess(int,int)'),self,QtCore.SLOT('updateUploadProcess(int,int)'))
        upload_thread.start()        
        event.acceptProposedAction();
        

class AuthorizeWindow(QtGui.QDialog):
    def __init__(self,parent=None):
        QtGui.QDialog.__init__(self,parent)
        fl = QtGui.QFormLayout()
        lbl=QtGui.QLabel("Please, log in with your Google Account")
        fl.addRow(lbl)
        self.username_edit = QtGui.QLineEdit()
        self.password_edit = QtGui.QLineEdit()
        self.password_edit.setEchoMode(QtGui.QLineEdit.Password)
        fl.addRow('Username',self.username_edit)
        fl.addRow('Password',self.password_edit)
        hl = QtGui.QHBoxLayout()
        ok = QtGui.QPushButton()
        ok.setText('Login')        
        ok.clicked.connect(self.tryLogin)
        exit = QtGui.QPushButton()
        exit.setText('Exit')
        hl.addWidget(ok)
        hl.addWidget(exit)        
        exit.clicked.connect(sys.exit)
        fl.addRow(hl)
        self.setLayout(fl)
        self.gd_client=None
        self.setModal(True)
    
    def getGdClient(self):
        return self.gd_client
        
    def tryLogin(self):
        self.gd_client = gdata.photos.service.PhotosService()
        if self.username_edit.text().contains('@'):
            self.gd_client.email = self.username_edit.text()
        else:
            self.gd_client.email = self.username_edit.text()+'@gmail.com'
        self.gd_client.password = self.password_edit.text()
        self.gd_client.source = 'qpypicassa'
        try:
            self.gd_client.ProgrammaticLogin()
        except:
            self.gd_client=None
        return self.accept()
#albums = gd_client.GetUserFeed(user='simakazi')
#for album in albums.entry:
#    combo.addItem('%s (%s)' % (album.title.text,album.numphotos.text),album.gphoto_id.text)
#print 'title: %s, number of photos: %s, id: %s' % (album.title.text, album.numphotos.text, album.gphoto_id.text)
  
#album = gd_client.InsertAlbum(title='New album', summary='This is an album')

QtCore.QTextCodec.setCodecForTr(QtCore.QTextCodec.codecForName("UTF-8"));
QtCore.QTextCodec.setCodecForCStrings(QtCore.QTextCodec.codecForName("UTF-8"));


gd_client=None
while gd_client is None:
    dialog=AuthorizeWindow()
    dialog.exec_()    
    gd_client = dialog.getGdClient()    
main = MainWindow(gd_client)
main.show()
sys.exit(app.exec_())