// Minimal self-contained ZIP32 archive writer using original zlib DEFLATE.
// It streams content, records CRC32 per file, commits via atomic rename and
// never deletes original logs until the archive has been fully written.
#include "zip_log_archive.h"
#include <zlib.h>
#include <array>
#include <algorithm>
#include <fstream>
#include <stdexcept>
#include <vector>
#include <limits>
#include <ctime>
#include <cstring>
#include <sys/stat.h>
namespace joshua_zip {
static void must(bool v, const std::string& reason){if(!v)throw std::runtime_error("ZIP: "+reason);}
static void u16(std::ostream&f,std::uint16_t n){f.put(char(n&255));f.put(char((n>>8)&255));}
static void u32(std::ostream&f,std::uint32_t n){u16(f,std::uint16_t(n));u16(f,std::uint16_t(n>>16));}
static std::uint32_t pos(std::ostream&f){auto n=f.tellp();must(n>=0&&std::uint64_t(n)<=UINT32_MAX,"ZIP32 offset exceeds 4 GiB");return std::uint32_t(n);}
static std::pair<std::uint16_t,std::uint16_t> dosTime(){
  std::time_t t=std::time(nullptr);std::tm tm{};localtime_r(&t,&tm);
  unsigned year=static_cast<unsigned>(tm.tm_year+1900);
  year=std::max(1980u,std::min(2107u,year));
  return {std::uint16_t((unsigned(tm.tm_hour)<<11)|(unsigned(tm.tm_min)<<5)|(unsigned(tm.tm_sec)/2)),
          std::uint16_t(((year-1980)<<9)|(unsigned(tm.tm_mon+1)<<5)|unsigned(tm.tm_mday))};
}
struct Central {std::string name;std::uint32_t crc=0,raw=0,compressed=0,offset=0;};
std::uint64_t directorySize(const fs::path& dir){
  std::uint64_t n=0;if(!fs::exists(dir))return 0;
  for(const auto&e:fs::recursive_directory_iterator(dir,fs::directory_options::skip_permission_denied)){
    must(!e.is_symlink(),"symlink in session directory: "+e.path().string());
    if(e.is_regular_file()){
      auto s=e.file_size();must(n<=UINT64_MAX-s,"directory size overflow");n+=s;
    }
  }return n;
}
ArchiveResult zipDirectoryAtomically(const fs::path& dir,const fs::path& target){
  must(fs::is_directory(dir),"input directory does not exist");
  must(!fs::exists(target),"refusing to overwrite an existing archive: "+target.string());
  fs::create_directories(target.parent_path());
  const fs::path temp=fs::path(target.string()+".part");
  // Leftover from SIGKILL or power loss: a .part file is never a commit.
  if(fs::exists(temp)){must(fs::is_regular_file(temp),"unsafe .part path");fs::remove(temp);}
  ArchiveResult stats;
  try{
    std::vector<fs::path> files;
    for(const auto&e:fs::recursive_directory_iterator(dir)){
      must(!e.is_symlink(),"symlink rejected: "+e.path().string());
      if(e.is_regular_file())files.push_back(e.path());
      else must(e.is_directory(),"unsupported file type: "+e.path().string());
    }
    must(files.size()<=65535,"ZIP32 file count limit reached");
    std::sort(files.begin(),files.end());
    std::ofstream out(temp,std::ios::binary|std::ios::trunc);
    must(bool(out),"cannot create "+temp.string());
    const auto clock=dosTime();
    std::vector<Central> entries;
    std::array<unsigned char,65536> in{},obuf{};
    for(const auto& file:files){
      Central c;
      c.name=fs::relative(file,dir).generic_string();
      must(!c.name.empty()&&c.name.size()<=65535&&c.name[0]!='/'&&c.name.find("../")==std::string::npos,"unsafe ZIP entry name");
      must(fs::file_size(file)<=UINT32_MAX,"ZIP32 single-file size limit reached");
      c.raw=static_cast<std::uint32_t>(fs::file_size(file));
      stats.source_bytes+=c.raw;
      c.offset=pos(out);
      // bit 3 = CRC/length descriptor follows the payload; bit 11 = UTF-8
      u32(out,0x04034b50);u16(out,20);u16(out,0x0808);u16(out,8);
      u16(out,clock.first);u16(out,clock.second);
      u32(out,0);u32(out,0);u32(out,0);
      u16(out,std::uint16_t(c.name.size()));u16(out,0);out.write(c.name.data(),std::streamsize(c.name.size()));
      std::ifstream src(file,std::ios::binary);must(bool(src),"cannot read "+file.string());
      z_stream zs{};
      must(deflateInit2(&zs,Z_DEFAULT_COMPRESSION,Z_DEFLATED,-MAX_WBITS,8,Z_DEFAULT_STRATEGY)==Z_OK,"deflate initialization failed");
      bool ended=false;
      try {
        uLong checksum=crc32(0L,Z_NULL,0);
        std::uint64_t compressed=0;
        while(true){
          src.read(reinterpret_cast<char*>(in.data()),std::streamsize(in.size()));
          const auto got=src.gcount();
          must(!src.bad(),"read failure: "+file.string());
          const int flush=(got==0)?Z_FINISH:Z_NO_FLUSH;
          if(got)checksum=crc32(checksum,in.data(),static_cast<uInt>(got));
          zs.next_in=in.data();zs.avail_in=static_cast<uInt>(got);
          int r=Z_OK;
          do{
            zs.next_out=obuf.data();zs.avail_out=static_cast<uInt>(obuf.size());
            r=deflate(&zs,flush);
            must(r==Z_OK||r==Z_STREAM_END,"deflate failed: "+file.string());
            const size_t count=obuf.size()-zs.avail_out;
            out.write(reinterpret_cast<const char*>(obuf.data()),std::streamsize(count));
            must(bool(out),"write failure");compressed+=count;
            must(compressed<=UINT32_MAX,"ZIP32 compressed file length exceeded");
          }while(zs.avail_out==0||(flush==Z_FINISH&&r!=Z_STREAM_END));
          if(flush==Z_FINISH)break;
        }
        must(zs.total_in==c.raw,"source file changed during compression: "+file.string());
        c.crc=static_cast<std::uint32_t>(checksum);c.compressed=static_cast<std::uint32_t>(compressed);
        deflateEnd(&zs);ended=true;
      }catch(...){if(!ended)deflateEnd(&zs);throw;}
      u32(out,0x08074b50);u32(out,c.crc);u32(out,c.compressed);u32(out,c.raw);
      entries.push_back(c);
    }
    const std::uint32_t centralStart=pos(out);
    for(const auto&c:entries){
      u32(out,0x02014b50);u16(out,0x031e);u16(out,20);
      u16(out,0x0808);u16(out,8);u16(out,clock.first);u16(out,clock.second);
      u32(out,c.crc);u32(out,c.compressed);u32(out,c.raw);
      u16(out,std::uint16_t(c.name.size()));u16(out,0);u16(out,0);
      u16(out,0);u16(out,0);u32(out,0);u32(out,c.offset);
      out.write(c.name.data(),std::streamsize(c.name.size()));
    }
    const std::uint32_t centralEnd=pos(out);
    u32(out,0x06054b50);u16(out,0);u16(out,0);
    u16(out,std::uint16_t(entries.size()));u16(out,std::uint16_t(entries.size()));
    u32(out,centralEnd-centralStart);u32(out,centralStart);u16(out,0);
    out.flush();must(bool(out),"failed to flush archive");out.close();
    must(bool(out),"failed to close archive");
    stats.files=entries.size();stats.compressed_bytes=fs::file_size(temp);
    fs::rename(temp,target); // Atomic on the same filesystem.
    return stats;
  }catch(...){std::error_code ec;fs::remove(temp,ec);throw;}
}
std::uint64_t allocatedBytes(const fs::path&p){
 struct stat info{};
 must(::stat(p.c_str(),&info)==0,"cannot stat file: "+p.string());
 return std::max<std::uint64_t>(std::uint64_t(info.st_size),std::uint64_t(info.st_blocks)*512);
}
static bool isManaged(const fs::path&p){
  auto s=p.filename().string();
  if(p.extension()!=".zip")return false;
  if(s.rfind("game_",0)!=0)return false;
  const auto digits=s.substr(5,s.size()-9);
  if(digits.empty())return false;
  return std::all_of(digits.begin(),digits.end(),[](unsigned char c){return c>='0'&&c<='9';});
}
std::uint64_t pruneArchives(const fs::path&folder,std::uint64_t budgetBytes,std::size_t* deleted){
  if(deleted)*deleted=0;
  if(!fs::exists(folder))return 0;
  std::vector<fs::path> zipFiles;
  std::uint64_t total=0;
  for(const auto&e:fs::directory_iterator(folder))if(e.is_regular_file()&&isManaged(e.path())){
    const auto s=allocatedBytes(e.path());must(total<=UINT64_MAX-s,"archive size overflow");total+=s;zipFiles.push_back(e.path());
  }
  std::sort(zipFiles.begin(),zipFiles.end()); // Stable ascending game IDs = oldest first.
  for(const auto&file:zipFiles){
    if(total<=budgetBytes)break;
    const auto size=allocatedBytes(file);
    fs::remove(file);total-=size;
    if(deleted)++*deleted;
  }
  return total;
}
}
