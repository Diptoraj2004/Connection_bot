class MusicPlatformService {
  constructor() {
    this.platforms = {
      youtube: {
        name: 'YouTube',
        searchUrl: 'https://www.youtube.com/results?search_query=',
        playUrl: 'https://www.youtube.com/watch?v='
      },
      spotify: {
        name: 'Spotify',
        searchUrl: 'https://open.spotify.com/search/',
        playUrl: 'https://open.spotify.com/track/'
      }
    };
  }

  searchSong(query, platform = 'youtube') {
    const platformConfig = this.platforms[platform];
    if (!platformConfig) return null;

    const searchQuery = encodeURIComponent(query);
    return `${platformConfig.searchUrl}${searchQuery}`;
  }

  async searchYouTubeVideos(query) {
    // Note: You'll need YouTube API key for this
    const API_KEY = process.env.REACT_APP_YOUTUBE_API_KEY;
    const url = `https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=5&q=${encodeURIComponent(query)}&key=${API_KEY}`;
    
    try {
      const response = await fetch(url);
      const data = await response.json();
      return data.items || [];
    } catch (error) {
      console.error('YouTube search error:', error);
      return [];
    }
  }

  openInPlatform(song, platform) {
    const url = this.searchSong(song.searchQuery, platform);
    window.open(url, '_blank');
  }
}

export default new MusicPlatformService();
