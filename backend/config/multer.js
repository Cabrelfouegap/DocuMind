const multer = require('multer');
const path = require('path');

const myStorageConfiguration = multer.diskStorage({
  destination: (request, file, callbackFunction) => {
    callbackFunction(null, path.join(__dirname, '..', 'uploads'));
  },
  filename: (request, file, callbackFunction) => {
    const currentTime = Date.now();
    const randomNumber = Math.round(Math.random() * 1000000000);
    const fileExtension = path.extname(file.originalname);
    const finalFileName = currentTime + '-' + randomNumber + fileExtension;
    
    callbackFunction(null, finalFileName);
  },
});

const myFileFilterFunction = (request, file, callbackFunction) => {
  const allowedTypes = [
    'application/pdf', 
    'image/png', 
    'image/jpeg', 
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ];

  if (allowedTypes.indexOf(file.mimetype) !== -1) {
    callbackFunction(null, true);
  } else {
    const myError = new Error('This file type is not supported by DocuMind');
    callbackFunction(myError, false);
  }
};

const uploader = multer({ 
  storage: myStorageConfiguration, 
  fileFilter: myFileFilterFunction 
});

module.exports = uploader;
