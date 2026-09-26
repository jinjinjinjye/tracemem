# Test scenarios: held outside this repository until the freeze

This folder stays empty until the team tags `freeze-v1`.

The test authors keep their scenarios outside this public repository until then, because anything committed here can be read by everyone, including the people who write prompts. At sealing time a decision record adds one file, `SHA256SUMS`, listing a SHA-256 digest per scenario file. After the freeze tag, the scenarios are added in a commit that changes nothing else, and anyone can check them against the digests with `sha256sum -c SHA256SUMS`.

See the working agreement, section 3.
