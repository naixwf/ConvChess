import caffe
import pgn
import chess
import argparse
from util import *
import timeit
import play.play3 as Play 
import progressbar

#parser2=argparse.ArgumentParser(description='Plot results for Move Number vs Error rate')

def add_arguments(parser):
	parser.add_argument('--file', dest='file',type=str, help='input file')
	parser.add_argument('--no-elolayer', dest='elolayer', action='store_false')
	parser.add_argument('--no-piecelayer', dest='piecelayer', action='store_false')
	parser.add_argument('--no-multilayer', dest='multilayer', action='store_false')
	parser.add_argument('--C', type=float, default=1255, 
		help='Divide the ELO rating minus Min ELO rating by this value')
	parser.add_argument('--saveplot', type=str, default='',
		help='The path of the file to save the plot to. Use extension also (pdf, png etc.)')
	parser.add_argument('--skip', type=int, help='skip first these many games.\
	Ideally a multiple of %d'%NUM_GAMES, default=0)
	parser.set_defaults(elolayer=True)
	parser.set_defaults(piecelayer=True)
	parser.set_defaults(multilayer=True)

#add_arguments(parser2)
#Play.add_arguments(parser)
#args = parser2.parse_args()


#if args.multilayer:
bitboard_to_image = convert_bitboard_to_image_2
flip_color = flip_color_2
# else:
# 	bitboard_to_image = convert_bitboard_to_image_1
# 	flip_color = flip_color_1

#max_len = max([len(game) for game in movelists])
max_len = 1000
correct_preds = np.zeros((max_len,30))
num_moves_arr = np.zeros(max_len)
#[[0 for j in xrange(30)] for i in xrange(max_len)] #holds the top-1,3,5,10 predictions
#hits = [(0,0) for i in xrange(max_len)]

# board_images_lists = []
# legal_moves_lists = []
# movelists = []
min_elo = 2000
max_elo = 3255
max_len = 0 
C=1255
num_games = 0
f = "sample2.pgn"
Play.load_models("play/models")
stop = False
for game in pgn.GameIterator(f):
	if num_games%10 == 0:
		print "Done with %d games"%num_games
	if (not game) or stop:	break
	num_games+=1
	board = chess.Bitboard()
	moves = game.moves
	max_len = max(len(moves), max_len)
	# board_images = []
	# movelist = []
	# legal_moves_list = []
	black_elo = int(game.blackelo)
	white_elo = int(game.whiteelo)		
	#if args.elolayer:
	white_elo_layer = float(white_elo - min_elo)/C
	black_elo_layer = float(black_elo- min_elo)/C
	bar = progressbar.ProgressBar(maxval=len(moves), \
    widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
  	bar.start()
	for move_index, move in enumerate(moves):
		bar.update(move_index+1)
		if move[0].isalpha() and not stop: # check if move is SAN
				try:
					from_to_chess_coords = board.parse_san(move)
				except ValueError:
					break
				from_to_chess_coords = str(from_to_chess_coords)
			
				from_chess_coords = from_to_chess_coords[:2]
				to_chess_coords = from_to_chess_coords[2:4]
				from_coords = chess_coord_to_coord2d(from_chess_coords)
				to_coords = chess_coord_to_coord2d(to_chess_coords)
				lmlist = [str(i) for i in board.legal_moves]
				lmlist = [(chess_coord_to_coord2d(i[:2]),chess_coord_to_coord2d(i[2:4])) for i in lmlist]			
				if move_index % 2 == 0:
					im = bitboard_to_image(board)
					#if args.elolayer:
					last_layer = white_elo_layer*np.ones((1,8,8))
				else:
					im = flip_image(bitboard_to_image(board))
					im = flip_color(im)
					from_coords = flip_coord2d(from_coords)
					to_coords = flip_coord2d(to_coords)
					lmlist = [(flip_coord2d(i[0]),flip_coord2d(i[1])) for i in lmlist]
					#if args.elolayer:
					last_layer = black_elo_layer*np.ones((1,8,8))

				index_piece = np.where(im[from_coords] == 1)
				# index_piece denotes the index in PIECE_TO_INDEX
				index_piece = index_piece[0][0]/2 # ranges from 0 to 5

				from_coords = flatten_coord2d(from_coords)
				to_coords = flatten_coord2d(to_coords)

				im = np.rollaxis(im, 2, 0) # to get into form (C, H, W)
				#if args.elolayer:
				im = np.append(im, last_layer, axis=0)
				
				board.push_san(move)
				lmlist = [(i[0][0]*8+i[0][1],i[1][0]*8+i[1][1]) for i in lmlist]
				# legal_moves_list.append(lmlist)
				# board_images.append(im)

				move = (from_coords,to_coords)
				try:
					#pred_moves = Play.get_move_prediction(im)
					pred_moves_vals = Play.get_top_moves(im, k=30, clipping=False)
					pred_moves = []
					for (m, v) in pred_moves_vals:
						from_chess_coords = m[:2]
						to_chess_coords = m[2:4]
						from_coords = chess_coord_to_coord2d(from_chess_coords)
						to_coords = chess_coord_to_coord2d(to_chess_coords)
						pred_moves.append((from_coords[0]*8+from_coords[1], to_coords[0]*8+to_coords[1]))
				except KeyboardInterrupt:
					stop = True
					break
				#print pred_moves, move
				#print pred_move, move, lmlist
				#pred_move = move
				#(a,b,c,d,e,f,g) = predictions[move_index]
				num_moves_arr[move_index]+=1
				try:
					pos = pred_moves.index(move)
					for j in range(pos,30):
						correct_preds[move_index,j]+=1
				except ValueError:
					pass
					
				# if index :
				# 	predictions[move_index]=(a+1,b+1,c+1,d+1,e+1)
				# elif move in pred_moves[:3]:
				# 	predictions[move_index]=(a,b+1,c+1,d+1,e+1)

				# else:
				# 	predictions[move_index]=(predictions[move_index][0],predictions[move_index][1]+1)
				#print pred_move, lmlist
				# for pred_move in pred_moves:
				# 	if pred_move in lmlist:
				# 		hits[move_index] = (hits[move_index][0]+1,hits[move_index][1]+1)
				# 	else:
				# 		hits[move_index] = (hits[move_index][0],hits[move_index][1]+1)
				# movelist.append((from_coords,to_coords))					
				#end = timeit.default_timer()
	# movelists.append(movelist)
	# board_images_lists.append(board_images)
	# legal_moves_lists.append(legal_moves_list)

#print correct_preds
#max_len = max([len(game) for game in movelists])
max_len = max_len - 2
correct_preds = correct_preds[:max_len]
num_moves_arr = num_moves_arr[:max_len]
accuracies = correct_preds/num_moves_arr[:,None]
import matplotlib.pyplot as plt
colors = ['k','b','g','r','m','c','y']
for j,i in enumerate([1,5,10,20,30]):
	plt.plot(accuracies[:,i-1],colors[j-1], label='k=%d'%i)
plt.legend(loc='lower right', numpoints =1)
plt.xlabel('Move Number in the game')
plt.ylabel('Move Accuracy')
plt.suptitle('Accuracy vs Move number for %d games'%num_games, fontsize=20, family='serif')
plt.show()

mean_accuracies = sum(correct_preds,1)/sum(num_moves_arr)
plt.plot(range(1,31),mean_accuracies,'g^-')
plt.xlabel('Number of guesses')
plt.ylabel('Mean Accuracy')
plt.show()

#hits = hits[:max_len]
# print max_len
# print predictions, hits

# accuracies = [[float(a)/g, float(b)/g, float(c)/g, float(d)/g, float(e)/g, float(f)/g] for (a,b,c,d,e,f,g) in predictions]
# import matplotlib.pyplot as plt
# accuracies = np.array(accuracies)
# plt.plot(accuracies[:,0],'k', label='Accuracy at k=1')
# plt.plot(accuracies[:,1], 'b', label='Accuracy at k=3')
# plt.plot(accuracies[:,2], 'g', label='Accuracy at k=5')
# plt.plot(accuracies[:,3], 'r', label='Accuracy at k=10')
# plt.plot(accuracies[:,4], 'c', label='Accuracy at k=20')
# plt.plot(accuracies[:,5], 'y', label='Accuracy at k=30')
# plt.legend( loc='upper right', numpoints = 1 )
# plt.xlabel('Move Number in the game')
# plt.ylabel('Accuracy')
# plt.suptitle('Accuracy vs Move number for %d games'%num_games, fontsize=20, family='serif')
# plt.show()

# predictions = np.array(predictions, dtype='float32')
# predictions=sum(predictions)
# [a,b,c,d,e,f,g] =predictions
# mean_accuracies = [a/g,b/g,c/g,d/g,e/g,f/g]
# print mean_accuracies

# hitrates = [float(hits[i][0])/hits[i][1] for i in xrange(max_len)]
# plt.plot(hitrates)
# plt.xlabel('Move Number in the game')
# plt.ylabel('Hit Rate')
# plt.suptitle('Hit Rate vs Move number for %d games'%num_games, fontsize=20, family='serif')
# plt.show()


# if args.saveplot:
	# plt.savefig(args.saveplot)




