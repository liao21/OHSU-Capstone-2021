/* global blueimp, $ */

$(function () {
    'use strict';

    // Initialize the Gallery as image carousel:
    blueimp.Gallery([
        {
        title: 'No Movement',
        href:  'img_arm_motions/No_Movement.png',
        type: 'image/png',
        thumbnail: 'img_arm_motions/No_Movement.png'
        },
        {
        title: 'Elbow Flexion',
        href:  'img_arm_motions/Elbow_Flexion.png',
        type: 'image/png',
        thumbnail: 'img_arm_motions/Elbow_Flexion.png'
        },
        {
        title: 'Elbow Extension',
        href:  'img_arm_motions/Elbow_Extension.png',
        type: 'image/png',
        thumbnail: 'img_arm_motions/Elbow_Extension.png'
        },
        {
        title: 'Wrist Rotate In',
        href:  'img_arm_motions/Wrist_Rotate_In.png',
        type: 'image/png',
        thumbnail: 'img_arm_motions/Wrist_Rotate_In.png'
        },
        {
        title: 'Wrist Rotate Out',
        href:  'img_arm_motions/Wrist_Rotate_Out.png',
        type: 'image/png',
        thumbnail: 'img_arm_motions/Wrist_Rotate_Out.png'
        },
        {
        title: 'Wrist Flex In',
        href:  'img_arm_motions/Wrist_Flexion.png',
        type: 'image/png',
        thumbnail: 'img_arm_motions/Wrist_Flexion.png'
        },
        {
        title: 'Wrist Extend Out',
        href:  'img_arm_motions/Wrist_Extension.png',
        type: 'image/png',
        thumbnail: 'img_arm_motions/Wrist_Extension.png'
        },
        {
        title: 'Hand Open',
        href:  'img_grasps/Hand_Open.png',
        type: 'image/png',
        thumbnail: 'img_grasps/Hand_Open.png'
        },
        {
        title: 'Spherical Grasp',
        href:  'img_grasps/Spherical_Grasp.png',
        type: 'image/png',
        thumbnail: 'img_grasps/Spherical_Grasp.png'
        },
        {
        title: 'Tip Grasp',
        href:  'img_grasps/Tip_Grasp.png',
        type: 'image/png',
        thumbnail: 'img_grasps/Tip_Grasp.png'
        },
        {
        title: 'Three Finger Pinch Grasp',
        href:  'img_grasps/Tripod_Grasp.bmp',
        },
        {
        title: 'Lateral Grasp',
        href:  'img_grasps/Hook_Grasp.bmp',
        },
        {
        title: 'Cylindrical Grasp',
        href:  'img_grasps/Hook_Grasp.bmp',
        },
        {
        title: 'Point Grasp',
        href:  'img_grasps/Trigger_Grasp.png',
        },
        {
        title: 'Hand Open',
        href:  'img_grasps/GEN3_Hand_Open.png',
        type: 'image/png',
        thumbnail: 'img_arm_motions/GEN3_Hand_Open.png'
        },
        {
        title: 'Index',
        href:  'img_grasps/GEN3_Index.png',
        type: 'image/png',
        thumbnail: 'img_arm_motions/GEN3_Index.png'
        },
        {
        title: 'Middle',
        href:  'img_grasps/GEN3_Middle.png',
        type: 'image/png',
        thumbnail: 'img_arm_motions/GEN3_Middle.png'
        },
        {
        title: 'Ring',
        href:  'img_grasps/GEN3_Ring.png',
        type: 'image/png',
        thumbnail: 'img_arm_motions/GEN3_Ring.png'
        },
        {
        title: 'Little',
        href:  'img_grasps/GEN3_Little.png',
        type: 'image/png',
        thumbnail: 'img_arm_motions/GEN3_Little.png'
        },
        {
        title: 'Thumb',
        href:  'img_grasps/GEN3_Thumb.png',
        type: 'image/png',
        thumbnail: 'img_arm_motions/GEN3_Thumb.png'
        },
        {
        title: 'Ring-Middle',
        href:  'img_grasps/GEN3_RingMiddle.png',
        type: 'image/png',
        thumbnail: 'img_arm_motions/GEN3_Thumb.png'
        },
        {
        title: 'The Bird',
        href:  'img_grasps/GEN3_Bird.png',
        type: 'image/png',
        thumbnail: 'img_arm_motions/GEN3_Thumb.png'
        },
    ], {
        container: '#blueimp-image-carousel',
        carousel: true,
        onslide: function (index, slide) {
                // Callback function executed on slide change.
                // Note these class commands must match those listed in pattern_rec\__init__.py class TrainingData
                console.log(slide.firstChild.title)
                sendCmd("Cls:" + slide.firstChild.title);
        }
    });
}); // function
