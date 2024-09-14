import {
  buildCSS,
  buildJS,
  generateManifest,
  runTests,
  watchJS,
} from '@hypothesis/frontend-build';
import gulp from 'gulp';
import changed from 'gulp-changed';
import gulpIf from 'gulp-if';
import svgmin from 'gulp-svgmin';

import tailwindConfig from './tailwind.config.js';

const IS_PRODUCTION_BUILD = process.env.NODE_ENV === 'production';

gulp.task('build-js', () => buildJS('./rollup.config.js'));
gulp.task('watch-js', () => watchJS('./rollup.config.js'));

gulp.task('build-legacy-css', () =>
  buildCSS([
    './node_modules/bootstrap/dist/css/bootstrap.css',
    './h/static/styles/admin.scss',
    './h/static/styles/help-page.scss',
    './h/static/styles/site.scss',
    './h/static/styles/vendor/icomoon.css',
  ]),
);

gulp.task('build-tailwind-css', () =>
  buildCSS(['./h/static/styles/group-forms.css'], { tailwindConfig }),
);

gulp.task('build-css', gulp.parallel('build-legacy-css', 'build-tailwind-css'));

gulp.task('watch-css', () => {
  gulp.watch(
    ['h/static/styles/**/*.{css,scss}', 'h/static/scripts/**/*.{js,ts,tsx}'],
    { ignoreInitial: false },
    gulp.series('build-css'),
  );
});

const fontFiles = 'h/static/styles/vendor/fonts/h.woff';

gulp.task('build-fonts', () => {
  const fontsDir = 'build/fonts';
  return gulp
    .src(fontFiles, { encoding: false })
    .pipe(changed(fontsDir))
    .pipe(gulp.dest(fontsDir));
});

gulp.task('watch-fonts', () => {
  gulp.watch(fontFiles, gulp.series('build-fonts'));
});

const imageFiles = 'h/static/images/**/*';

gulp.task('build-images', () => {
  const shouldMinifySVG = function (file) {
    return IS_PRODUCTION_BUILD && file.path.match(/\.svg$/);
  };

  // See https://github.com/ben-eb/gulp-svgmin#plugins
  const svgminConfig = {
    plugins: [
      {
        // svgo removes `viewBox` by default, which breaks scaled rendering of
        // the SVG.
        //
        // See https://github.com/svg/svgo/issues/1128
        name: 'removeViewBox',
        active: false,
      },
    ],
  };

  const imagesDir = 'build/images';
  return gulp
    .src(imageFiles, {
      // Treat all files as binary. Some of the images are SVGs which are text,
      // but `svgmin` is still able to process the files if passed as binary.
      encoding: false,
    })
    .pipe(changed(imagesDir))
    .pipe(gulpIf(shouldMinifySVG, svgmin(svgminConfig)))
    .pipe(gulp.dest(imagesDir));
});

gulp.task('watch-images', () => {
  gulp.watch(imageFiles, gulp.series('build-images'));
});

const MANIFEST_SOURCE_FILES = 'build/@(fonts|images|scripts|styles)/**/*.*';

gulp.task('build-manifest', () =>
  generateManifest({ pattern: MANIFEST_SOURCE_FILES }),
);
gulp.task('watch-manifest', () => {
  gulp.watch(MANIFEST_SOURCE_FILES, gulp.series('build-manifest'));
});

gulp.task(
  'build',
  gulp.series(
    gulp.parallel(['build-js', 'build-css', 'build-fonts', 'build-images']),
    'build-manifest',
  ),
);
gulp.task(
  'watch',
  gulp.parallel([
    'watch-js',
    'watch-css',
    'watch-fonts',
    'watch-images',
    'watch-manifest',
  ]),
);

gulp.task('test', () =>
  runTests({
    bootstrapFile: './h/static/scripts/tests/bootstrap.js',
    karmaConfig: './h/static/scripts/karma.config.cjs',
    rollupConfig: './rollup-tests.config.js',
    testsPattern: 'h/static/scripts/**/*-test.js',
  }),
);
