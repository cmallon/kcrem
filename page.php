<?php
/**
 * The template for displaying all pages.
 *
 * This is the template that displays all pages by default.
 * Please note that this is the WordPress construct of pages
 * and that other 'pages' on your WordPress site will use a
 * different template.
 *
 * To generate specific templates for your pages you can use:
 * /mytheme/templates/page-mypage.twig
 * (which will still route through this PHP file)
 * OR
 * /mytheme/page-mypage.php
 * (in which case you'll want to duplicate this file and save to the above path)
 *
 * Methods for TimberHelper can be found in the /lib sub-directory
 *
 * @package  WordPress
 * @subpackage  Timber
 * @since    Timber 0.1
 */

$context = Timber::context();

$timber_post     = new Timber\Post();
$context['post'] = $timber_post;
$context["acf"] = get_field_objects($timber_post->ID);
$args = array(
    // Get post type project
    'post_type' => 'listings',
    // Get all posts
    'posts_per_page' => -1,
    // Order by post date
    'orderby' => array(
        'date' => 'DESC'
    ));
$context["listings"] = Timber::get_posts( $args );
Timber::render( array( 'page-' . $timber_post->post_name . '.twig', 'page.twig' ), $context );
