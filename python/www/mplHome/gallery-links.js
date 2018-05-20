/* global blueimp, $ */
/*

Populate the image carousel dynamically using the class name and image file name in  motion_name_image_map.csv

Revisions:
  27MAR2018 Armiger: Made this function dynamic

*/

function setupGalley() {
  // Create image gallery

  // Populate and Initialize the Gallery as image carousel:
  blueimp.Gallery(global_motion_class_data, {
    container: '#blueimp-image-carousel',
    carousel: true,
    onslide: function (index, slide) {
      // Callback function executed on slide change.
      // Note these class commands must match those listed in pattern_rec\__init__.py class TrainingData
      sendCmd("Cls:" + global_motion_class_data[index].title);
    }
  });
}
