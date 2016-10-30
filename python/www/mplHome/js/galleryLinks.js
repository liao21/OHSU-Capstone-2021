/*
 * blueimp Gallery Demo JS 2.11.1
 * https://github.com/blueimp/Gallery
 *
 * Copyright 2013, Sebastian Tschan
 * https://blueimp.net
 *
 * Licensed under the MIT license:
 * http://www.opensource.org/licenses/MIT
 */

/* global blueimp, $ */

$(function () {
    'use strict';

    // Initialize the Gallery as video carousel:
    blueimp.Gallery([
        {
        title: 'Elbow Flexion',
        href: 'locos/ADDR_01.jpg',
        type: 'image/jpeg',
        thumbnail: 'locos/ADDR_01.jpg'
        },
        {
        title: 'Elbow Extension',
        href: 'locos/ADDR_02.jpg',
        type: 'image/jpeg',
        thumbnail: 'locos/ADDR_02.jpg'
        },
        {
        title: 'Wrist Rotate In (Pronate)',
        href: 'locos/ADDR_03.jpg',
        type: 'image/jpeg',
        thumbnail: 'locos/ADDR_03.jpg'
        },
        {
        title: 'Wrist Rotate Out (Supinate)',
        href: 'locos/ADDR_04.jpg',
        type: 'image/jpeg',
        thumbnail: 'locos/ADDR_04.jpg'
        },
        {
        title: 'Wrist Flex In',
        href: 'locos/ADDR_05.jpg',
        type: 'image/jpeg',
        thumbnail: 'locos/ADDR_05.jpg'
        },
        {
        title: 'Wrist Extend Out',
        href: 'locos/ADDR_06.jpg',
        type: 'image/jpeg',
        thumbnail: 'locos/ADDR_06.jpg'
        },
        {
        title: 'Hand Open',
        href: 'locos/ADDR_07.jpg',
        type: 'image/jpeg',
        thumbnail: 'locos/ADDR_07.jpg'
        },
        {
        title: 'Spherical Grasp',
        href: 'locos/ADDR_08.jpg',
        type: 'image/jpeg',
        thumbnail: 'locos/ADDR_08.jpg'
        },
        {
        title: 'No Movement',
        href: 'locos/ADDR_09.jpg',
        type: 'image/jpeg',
        thumbnail: 'locos/ADDR_09.jpg'
        }      
    ], {
        container: '#loco-carousel',
        carousel: true,
        onslide: function (index, slide) {
                // Callback function executed on slide change.
                switch(index) {
                case 0: sendCmd("A1"); break;
                case 1: sendCmd("A2"); break;
                case 2: sendCmd("A3"); break;
                case 3: sendCmd("A4"); break;
                case 4: sendCmd("A5"); break;
                case 5: sendCmd("A6"); break;
                case 6: sendCmd("A7"); break;
                case 7: sendCmd("A8"); break;
                case 8: sendCmd("A9"); break;
                default: break;
                }        
        }
    });

}); // function
