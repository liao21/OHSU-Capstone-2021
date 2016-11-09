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
        title: 'Banana',
        href: 'http://thefitnessfairy.com/wp-content/uploads/2014/05/peeled-banana.jpg',
        type: 'image/jpeg',
        thumbnail: 'http://thefitnessfairy.com/wp-content/uploads/2014/05/peeled-banana.jpg'
        },
        {
        title: 'Orange',
        href: 'img/error.png',
        type: 'image/jpeg',
        thumbnail: 'img/error.png'
        }
    ], {
        container: '#blueimp-image-carousel',
        carousel: true
    });

});
