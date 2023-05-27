# unfortunately it's not easy to verify whether the subtitling program produces the intended image,
# and adding images as tests will take up quite a bit of unnecessary space
# so we will only check whether the subtitling program successfully produces an image to begin with.
# will test these at the controller level.

# TODO: mainly test the compose function.

# given a couple of (generated) images, and many various combinations of subtitle configurations, apply subtitles.
# given a couple images, and a script/draft, apply subtitles.
# given a couple images, several drafts, a styles.yml file, apply subtitles.
# given a couple images, a script, apply subtitles once with incremental update. Update draft then apply again.
# same thing but with images.
# same thing but with styles.
# same thing but run compose without incremental updating. Then run again with incremental updating.