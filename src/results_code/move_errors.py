import caffe
import pgn
import chess
import argparse
from util import *
import timeit
import play.play3 as Play 

parser=argparse.ArgumentParser(description='Plot results for Move Number vs Error rate')
parser.add_argument('--file', dest='file',type=str, help='input file')
parser.add_argument('--no-elolayer', dest='elolayer', action='store_false')
parser.add_argument('--no-piecelayer', dest='piecelayer', action='store_false')
parser.add_argument('--no-multilayer', dest='multilayer', action='store_false')
parser.add_argument('--C', type=float, default=1255, 
	help='Divide the ELO rating minus Min ELO rating by this value')
parser.add_argument('--saveplot', type=str, default='',
	help='The path of the file to save the plot to. Use extension also (pdf, png etc.)')
parser.set_defaults(elolayer=True)
parser.set_defaults(piecelayer=True)
parser.set_defaults(multilayer=True)
args = parser.parse_args()

if args.multilayer:
	bitboard_to_image = convert_bitboard_to_image_2
	flip_color = flip_color_2
else:
	bitboard_to_image = convert_bitboard_to_image_1
	flip_color = flip_color_1

#max_len = max([len(game) for game in movelists])
max_len = 500
predictions = [(0,0) for i in xrange(max_len)]
hits = [(0,0) for i in xrange(max_len)]

# board_images_lists = []
# legal_moves_lists = []
# movelists = []
min_elo = 2000
max_elo = 3255
max_len = 0 
for game in pgn.GameIterator(args.file):
	if not game:	break
	board = chess.Bitboard()
	moves = game.moves
	max_len = max(len(moves), max_len)
	# board_images = []
	# movelist = []
	# legal_moves_list = []
	black_elo = int(game.blackelo)
	white_elo = int(game.whiteelo)		
	if args.elolayer:
		white_elo_layer = float(white_elo - min_elo)/args.C
		black_elo_layer = float(black_elo- min_elo)/args.C
	for move_index, move in enumerate(moves):
		if move[0].isalpha(): # check if move is SAN
				from_to_chess_coords = board.parse_san(move)
				from_to_chess_coords = str(from_to_chess_coords)
			
				from_chess_coords = from_to_chess_coords[:2]
				to_chess_coords = from_to_chess_coords[2:4]
				from_coords = chess_coord_to_coord2d(from_chess_coords)
				to_coords = chess_coord_to_coord2d(to_chess_coords)
				lmlist = [str(i) for i in board.legal_moves]
				lmlist = [(chess_coord_to_coord2d(i[:2]),chess_coord_to_coord2d(i[2:4])) for i in lmlist]			
				if move_index % 2 == 0:
					im = bitboard_to_image(board)
					if args.elolayer:
						last_layer = white_elo_layer*np.ones((1,8,8))
				else:
					im = flip_image(bitboard_to_image(board))
					im = flip_color(im)
					from_coords = flip_coord2d(from_coords)
					to_coords = flip_coord2d(to_coords)
					lmlist = [(flip_coord2d(i[0]),flip_coord2d(i[1])) for i in lmlist]
					if args.elolayer:
						last_layer = black_elo_layer*np.ones((1,8,8))

				index_piece = np.where(im[from_coords] == 1)
				# index_piece denotes the index in PIECE_TO_INDEX
				index_piece = index_piece[0][0]/2 # ranges from 0 to 5

				from_coords = flatten_coord2d(from_coords)
				to_coords = flatten_coord2d(to_coords)

				im = np.rollaxis(im, 2, 0) # to get into form (C, H, W)
				if args.elolayer:
					im = np.append(im, last_layer, axis=0)
				
				board.push_san(move)
				lmlist = [(i[0][0]*8+i[0][1],i[1][0]*8+i[1][1]) for i in lmlist]
				# legal_moves_list.append(lmlist)
				# board_images.append(im)

				move = (from_coords,to_coords)
				pred_move = Play.get_move_prediction(im, 'play/models')
				#pred_move = move
				if pred_move == move:
					predictions[move_index]=(predictions[move_index][0]+1,predictions[move_index][1]+1)
				else:
					predictions[move_index]=(predictions[move_index][0],predictions[move_index][1]+1)
				#print pred_move, lmlist
				if pred_move in lmlist:
					hits[move_index] = (hits[move_index][0]+1,hits[move_index][1]+1)
				else:
					hits[move_index] = (hits[move_index][0],hits[move_index][1]+1)	
				# movelist.append((from_coords,to_coords))					
				end = timeit.default_timer()
	# movelists.append(movelist)
	# board_images_lists.append(board_images)
	# legal_moves_lists.append(legal_moves_list)


#max_len = max([len(game) for game in movelists])
max_len = max_len - 2
predictions = predictions[:max_len]
hits = hits[:max_len]
# print max_len
# print predictions, hits

errorrates = [1.0-float(pred[0])/pred[1] for pred in predictions]
import matplotlib.pyplot as plt
plt.plot(errorrates)
plt.xlabel('Move Number in the game')
plt.ylabel('Error Rate')
plt.suptitle('Error Rate vs Move number', fontsize=20, family='serif')
plt.show()

hitrates = [float(hits[i][0])/hits[i][1] for i in xrange(max_len)]
plt.plot(hitrates)
plt.xlabel('Move Number in the game')
plt.ylabel('Hit Rate')
plt.suptitle('Hit Rate vs Move number', fontsize=20, family='serif')
plt.show()


if args.saveplot:
	plt.savefig(args.saveplot)



