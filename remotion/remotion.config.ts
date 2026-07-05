// Remotion configuration for the v0.8 rendering prototype.
// See https://www.remotion.dev/docs/config for all options.
//
// These settings only affect local rendering and the Studio preview. The
// prototype is local-first and never uploads or publishes anything.
import {Config} from '@remotion/cli/config';

// Vertical short output, encoded as H.264 MP4.
Config.setVideoImageFormat('jpeg');
Config.setCodec('h264');

// Overwrite the previous render so re-running is deterministic and idempotent.
Config.setOverwriteOutput(true);
