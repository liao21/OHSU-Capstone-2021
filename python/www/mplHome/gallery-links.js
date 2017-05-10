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
        title: 'Wrist Rotate In (Pronate)',
        href:  'img_arm_motions/Wrist_Rotate_In.png',
        type: 'image/png',
        thumbnail: 'img_arm_motions/Wrist_Rotate_In.png'
        },
        {
        title: 'Wrist Rotate Out (Supinate)',
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
        title: 'Three Finger Pinch',
        href:  'img_grasps/ThreeFingerPinch.png',
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
        }
    ], {
        container: '#blueimp-image-carousel',
        carousel: true,
        onslide: function (index, slide) {
                // Callback function executed on slide change.
                // Note these class commands must match those listed in pattern_rec\__init__.py class TrainingData
                switch(index) {
                case  0: sendCmd("Cls:No Movement"); break;
                case  1: sendCmd("Cls:Elbow Flexion"); break;
                case  2: sendCmd("Cls:Elbow Extension"); break;
                case  3: sendCmd("Cls:Wrist Rotate In"); break;
                case  4: sendCmd("Cls:Wrist Rotate Out"); break;
                case  5: sendCmd("Cls:Wrist Flex In"); break;
                case  6: sendCmd("Cls:Wrist Extend Out"); break;
                case  7: sendCmd("Cls:Hand Open"); break;
                case  8: sendCmd("Cls:Spherical Grasp"); break;
                case  9: sendCmd("Cls:Tip Grasp"); break;
                case 10: sendCmd("Cls:Three Finger Pinch Grasp"); break;
                case 11: sendCmd("Cls:Lateral Grasp"); break;
                case 12: sendCmd("Cls:Cylindrical Grasp"); break;
                case 13: sendCmd("Cls:Point Grasp"); break;
                case 99: sendCmd("Cls:Index Grasp"); break;
                case 99: sendCmd("Cls:Middle Grasp"); break;
                case 99: sendCmd("Cls:Ring Grasp"); break;
                case 99: sendCmd("Cls:Little Grasp"); break;
                default: break;
                }        
        }
    });
}); // function
