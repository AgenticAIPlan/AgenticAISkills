/**
 * AgenticAISkills plugin for OpenCode.ai
 *
 * Registers the repository skills directory into OpenCode's runtime config
 * so the business skills in this repository can be discovered without
 * additional local symlink setup.
 */

import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export const AgenticAISkillsPlugin = async () => {
  const skillsDir = path.resolve(__dirname, '../../skills');

  return {
    config: async (config) => {
      config.skills = config.skills || {};
      config.skills.paths = config.skills.paths || [];

      if (!config.skills.paths.includes(skillsDir)) {
        config.skills.paths.push(skillsDir);
      }
    }
  };
};
