# -*- coding: utf-8 -*-
import praw, time, re, pickle, traceback, os, memcache
from util import success, warn, log, fail

### Set root directory to script directory
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

### Set memcache client
shared = memcache.Client(['127.0.0.1:11211'], debug=0)

r = praw.Reddit("autowikibot by /u/acini at /r/autowikibot")
deletekeyword = "delete"
excludekeyword = "leave me alone"

### Load saved data
global banned_users
banned_users = [line.strip() for line in open('banned_users')]
shared.set('banned_users',banned_users)

with open('totaldeleted') as f:
    deleted = pickle.load(f)
with open ('userpass', 'r') as myfile:
  lines=myfile.readlines()
USERNAME = lines[0].strip()
PASSWORD = lines[1].strip()

### Login
### Wiki_FirstPara_bot is old account
Trying = True
while Trying:
        try:
                r.login(USERNAME, PASSWORD)
                success("Logged in.")
                Trying = False
        except praw.errors.InvalidUserPass:
                fail("Wrong username or password.")
                exit()
        except Exception as e:
	  fail(e)
	  time.sleep(5)

while True:
  try:
    log("Comment score check cycle started")
    user = r.get_redditor(USERNAME)
    total = 0
    upvoted = 0
    unvoted = 0
    downvoted = 0
    for c in user.get_comments(limit=None):
      
      if len(str(c.score)) == 4:
	spaces = ""
      if len(str(c.score)) == 3:
	spaces = " "
      if len(str(c.score)) == 2:
	spaces = "  "
      if len(str(c.score)) == 1:
	spaces = "   "
      
      total = total + 1
      if c.score < 0:
	c.delete()
	print "\033[1;41m%s%s\033[1;m"%(spaces,c.score),
	deleted = deleted + 1
	downvoted = downvoted + 1
      elif c.score > 10:
	print "\033[1;32m%s%s\033[1;m"%(spaces,c.score),
	upvoted = upvoted + 1
      elif c.score > 1:
	print "\033[1;34m%s%s\033[1;m"%(spaces,c.score),
	upvoted = upvoted + 1
	#call (["firefox",c.permalink])
      elif c.score > 0:
	print "\033[1;30m%s%s\033[1;m"%(spaces,c.score),
	unvoted = unvoted + 1
      elif c.score < 1:
	print "\033[1;33m%s%s\033[1;m"%(spaces,c.score),
	downvoted = downvoted + 1
      
    print ("")
    log("Comment score check cycle completed")
    urate = round(upvoted / float(total) * 100)
    nrate = round(unvoted / float(total) * 100)
    drate = round(downvoted / float(total) * 100)
    log("Upvoted:      %s\t%s\b\b %%"%(upvoted,urate))
    log("Unvoted       %s\t%s\b\b %%"%(unvoted,nrate))
    log("Downvoted:    %s\t%s\b\b %%"%(downvoted,drate))
    log("Total:        %s"%total)
    
    with open('totaldeleted', 'w') as f:
      pickle.dump(deleted, f)
    log("Statistics saved")
    
    

    ### Check inbox 15 times
    log("Autodelete cycles started")
    for x in range(1, 16):
      log("Cycle %s"%x)
      try:
	unread = r.get_unread(limit=None)
	for msg in unread:
	  ### Remove comment 
	  if re.search(deletekeyword, msg.body.lower()) or re.search("\+remove", msg.body.lower()): #remove "+remove" for new bot username
	    try:
	      bot_comment_id = msg.parent_id
	      bot_comment = r.get_info(thing_id=bot_comment_id)
	      if bot_comment.author.name == USERNAME:
		bot_comment_parent = r.get_info(thing_id=bot_comment.parent_id)
		if msg.author.name == bot_comment_parent.author.name:
		  bot_comment.delete()
		  deleted = deleted + 1
		  success("Autodeletion @ %s"%bot_comment_parent.permalink)
		else:
		  #msg.reply ("*Sorry. Only /u/%s can trigger this delete.*"%bot_comment_parent.author.name)
		  fail("Bad autodelete request @ /u/%s"%bot_comment_parent.permalink)
	      else:
		if msg.author.name != USERNAME:
		  warn("Autodelete flag out of context @ %s"%bot_comment_parent.permalink)
		  continue
	      msg.mark_as_read()
	    except Exception as e:
	      if (str(e)=="'NoneType' object has no attribute 'name'"):
		bot_comment.delete()
		deleted = deleted + 1
		success("Autodeletion (orphan) @ %s"%bot_comment_parent.permalink)
	      else:
		fail("%s\033[1;m"%e)
	      msg.mark_as_read()
	      continue
	  else:
	    msg.mark_as_unread()
	  ### Add user to exclude list
	  if re.search(excludekeyword, msg.body.lower()):
	    with open('banned_users', 'a') as myfile:
	      myfile.write("%s\n"%msg.author.name)
	    msg.mark_as_read()
	    msg.reply("*Done! I won't reply to your comments now.*\n\n*Have a nice day!*")
	    ### Save user to arra
	    banned_users.append(msg.author.name)
	    shared.set('banned_users',banned_users)
	    success("Banned /u/%s"%msg.author.name)
	  time.sleep(1)
	time.sleep(60)
      except KeyboardInterrupt:
	with open('totaldeleted', 'w') as f:
	  pickle.dump(deleted, f)
	success("Statistics dumped to file.")
	exit()
      except Exception as e:
	traceback.print_exc()
	fail(e)
	time.sleep(3)
	continue
    log("Autodelete cycles completed.")
    with open('totaldeleted', 'w') as f:
      pickle.dump(deleted, f)
    success("Statistics saved.")
        
  except KeyboardInterrupt:
    with open('totaldeleted', 'w') as f:
	pickle.dump(deleted, f)
    success("Statistics dumped to file.")
    log("Bye!")
    break
  except Exception as e:
    traceback.print_exc()
    fail(e)
    time.sleep(3)
    continue
  