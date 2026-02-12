module.exports = {
  ci: {
    collect: {
      numberOfRuns: 5,
      staticDistDir: './ci-report',
      settings: {
        chromeFlags: '--no-sandbox --disable-gpu',
        disableStorageReset: true
      }
    },
    assert: {
      assertions: {
        'categories:accessibility': ['error', { minScore: 0.95 }]
      }
    },
    upload: {
      target: 'filesystem',
      outputDir: './lhci-results'
    }
  }
};
